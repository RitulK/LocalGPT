import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import database


DEFAULT_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
CHUNK_WORDS = int(os.getenv("RAG_CHUNK_WORDS", "800"))
CHUNK_OVERLAP_WORDS = int(os.getenv("RAG_CHUNK_OVERLAP_WORDS", "120"))
RETRIEVAL_LIMIT = int(os.getenv("RAG_RETRIEVAL_LIMIT", "5"))


class RAGService:
    """Document ingestion and retrieval for LocalGPT's knowledge base."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.upload_dir = self.base_dir / "uploads"
        self.chroma_dir = self.base_dir / "chroma"
        self.embedding_model = embedding_model
        self.collection_name = "localgpt_documents"
        self._collection = None

    def ensure_storage(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, filename: str, content_type: str) -> str:
        extension = Path(filename or "").suffix.lower()
        allowed_extensions = {".txt", ".pdf"}
        if extension not in allowed_extensions:
            raise ValueError("Only PDF and TXT files are supported.")

        allowed_content_types = {
            ".txt": {"text/plain", "application/octet-stream"},
            ".pdf": {"application/pdf", "application/octet-stream"},
        }
        if content_type and content_type not in allowed_content_types[extension]:
            raise ValueError("File type does not match the uploaded content.")

        return extension

    def safe_filename(self, filename: str) -> str:
        name = Path(filename or "document").name
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
        return name or "document"

    async def ingest_upload(self, upload_file, ollama_client) -> Dict[str, Any]:
        self.ensure_storage()
        self.validate_upload(upload_file.filename, upload_file.content_type or "")

        document = database.create_document(
            filename=self.safe_filename(upload_file.filename),
            content_type=upload_file.content_type or "application/octet-stream",
            file_path="pending",
            status="pending",
        )

        document_id = document["id"]
        filename = document["filename"]
        file_path = self.upload_dir / f"{document_id}-{filename}"
        content = await upload_file.read()
        file_path.write_bytes(content)
        database.update_document_file_path(document_id, str(file_path))

        try:
            await self.index_document(document_id, ollama_client)
        except Exception as exc:
            database.update_document_status(document_id, "failed", 0, str(exc))

        return database.get_document(document_id)

    async def index_document(self, document_id: int, ollama_client) -> Dict[str, Any]:
        document = database.get_document(document_id)
        if not document:
            raise ValueError("Document not found.")

        database.update_document_status(document_id, "indexing", error=None)
        pages = self.extract_text(Path(document["file_path"]))
        chunks = self.chunk_pages(pages)
        if not chunks:
            raise ValueError("No extractable text was found in this document.")

        embeddings = await self.embed_chunks(
            [chunk["content"] for chunk in chunks],
            ollama_client,
        )

        self.delete_document_vectors(document_id)
        collection = self.get_collection()
        collection.add(
            ids=[self.chunk_id(document_id, chunk["chunk_index"]) for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk["content"] for chunk in chunks],
            metadatas=[
                {
                    "document_id": document_id,
                    "filename": document["filename"],
                    "chunk_index": chunk["chunk_index"],
                    "page_number": chunk["page_number"] or -1,
                }
                for chunk in chunks
            ],
        )

        database.replace_document_chunks(document_id, chunks)
        database.update_document_status(document_id, "ready", len(chunks), error=None)
        return database.get_document(document_id)

    def extract_text(self, file_path: Path) -> List[Dict[str, Any]]:
        extension = file_path.suffix.lower()
        if extension == ".txt":
            return [{"page_number": None, "text": self.normalize_text(file_path.read_text(errors="replace"))}]
        if extension == ".pdf":
            return self.extract_pdf(file_path)
        raise ValueError("Unsupported document type.")

    def extract_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is not installed. Run pip install -r backend/requirements.txt.") from exc

        reader = PdfReader(str(file_path))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            text = self.normalize_text(page.extract_text() or "")
            if text:
                pages.append({"page_number": index, "text": text})
        return pages

    def chunk_pages(
        self,
        pages: List[Dict[str, Any]],
        chunk_words: int = CHUNK_WORDS,
        overlap_words: int = CHUNK_OVERLAP_WORDS,
    ) -> List[Dict[str, Any]]:
        chunks = []
        chunk_index = 0
        step = max(chunk_words - overlap_words, 1)

        for page in pages:
            words = page["text"].split()
            for start in range(0, len(words), step):
                window = words[start:start + chunk_words]
                if not window:
                    continue
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "page_number": page.get("page_number"),
                        "content": " ".join(window),
                    }
                )
                chunk_index += 1
                if start + chunk_words >= len(words):
                    break

        return chunks

    async def embed_chunks(self, texts: List[str], ollama_client, batch_size: int = 32) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            embeddings.extend(await ollama_client.embed(self.embedding_model, batch))
        if len(embeddings) != len(texts):
            raise RuntimeError("Embedding count did not match chunk count.")
        return embeddings

    async def retrieve(
        self,
        prompt: str,
        document_ids: List[int],
        ollama_client,
        limit: int = RETRIEVAL_LIMIT,
    ) -> List[Dict[str, Any]]:
        ready_document_ids = [
            document_id
            for document_id in document_ids
            if (database.get_document(document_id) or {}).get("status") == "ready"
        ]
        if not ready_document_ids:
            return []

        query_embedding = (await ollama_client.embed(self.embedding_model, [prompt]))[0]
        where = (
            {"document_id": ready_document_ids[0]}
            if len(ready_document_ids) == 1
            else {"document_id": {"$in": ready_document_ids}}
        )
        results = self.get_collection().query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        sources = []
        for index, content in enumerate(documents):
            metadata = metadatas[index] or {}
            page_number = metadata.get("page_number")
            sources.append(
                {
                    "source_index": index + 1,
                    "document_id": metadata.get("document_id"),
                    "filename": metadata.get("filename", "Document"),
                    "chunk_index": metadata.get("chunk_index"),
                    "page_number": None if page_number == -1 else page_number,
                    "distance": distances[index] if index < len(distances) else None,
                    "content": content,
                    "snippet": self.snippet(content),
                }
            )
        return sources

    def delete_document_vectors(self, document_id: int) -> None:
        try:
            self.get_collection().delete(where={"document_id": document_id})
        except Exception:
            pass

    def get_collection(self):
        if self._collection is None:
            try:
                import chromadb
            except ImportError as exc:
                raise RuntimeError("chromadb is not installed. Run pip install -r backend/requirements.txt.") from exc

            self.ensure_storage()
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def chunk_id(self, document_id: int, chunk_index: int) -> str:
        return f"document-{document_id}-chunk-{chunk_index}"

    def normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def snippet(self, text: str, max_chars: int = 280) -> str:
        normalized = self.normalize_text(text)
        if len(normalized) <= max_chars:
            return normalized
        return f"{normalized[:max_chars].rstrip()}..."
