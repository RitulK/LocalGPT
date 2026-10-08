import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import database
from app.infrastructure.vector.chroma_store import ChromaStore


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
        self.ensure_storage()
        self.chroma_store = ChromaStore(
            chroma_dir=self.chroma_dir,
            collection_name=self.collection_name,
        )

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

    async def save_upload(self, upload_file) -> Dict[str, Any]:
        self.ensure_storage()
        self.validate_upload(upload_file.filename, upload_file.content_type or "")

        document = database.create_document(
            filename=self.safe_filename(upload_file.filename),
            content_type=upload_file.content_type or "application/octet-stream",
            file_path="",
            status="pending",
        )
        document_id = document["id"]
        extension = Path(upload_file.filename or "").suffix.lower()
        file_path = self.upload_dir / f"doc_{document_id}{extension}"

        try:
            content = await upload_file.read()
            file_path.write_bytes(content)
            database.update_document_file_path(document_id, str(file_path))
        except Exception as exc:
            database.update_document_status(document_id, "failed", 0, str(exc))
            raise

        return database.get_document(document_id)

    async def ingest_upload(self, upload_file, ollama_client) -> Dict[str, Any]:
        # Deprecated: use save_upload + index_document for async ingestion
        document = await self.save_upload(upload_file)
        try:
            await self.index_document(document["id"], ollama_client)
        except Exception:
            pass # Error handled inside index_document
        return database.get_document(document["id"])


    async def index_document(self, document_id: int, ollama_client) -> Dict[str, Any]:
        document = database.get_document(document_id)
        if not document:
            raise ValueError("Document not found.")

        database.update_document_status(document_id, "indexing", error=None)
        try:
            file_path = Path(document["file_path"])
            text_by_page = self.extract_text(file_path, document["content_type"])
            chunks = self.chunk_pages(text_by_page)
            if not chunks:
                raise ValueError("No text could be extracted from document.")

            embeddings = await self.embed_chunks(
                [chunk["content"] for chunk in chunks],
                ollama_client,
            )
            collection = self.get_collection()
            collection.delete(where={"document_id": document_id})
            collection.add(
                ids=[self.chunk_id(document_id, idx) for idx in range(len(chunks))],
                embeddings=embeddings,
                documents=[chunk["content"] for chunk in chunks],
                metadatas=[
                    {
                        "document_id": document_id,
                        "filename": document["filename"],
                        "chunk_index": chunk["chunk_index"],
                        "page_number": chunk.get("page_number") or -1,
                    }
                    for chunk in chunks
                ],
            )
            database.replace_document_chunks(document_id, chunks)
            database.update_document_status(document_id, "ready", len(chunks), error=None)
            return database.get_document(document_id)
        except Exception as exc:
            database.update_document_status(document_id, "failed", error=str(exc))
            raise

    def extract_text(self, file_path: Path, content_type: str = "") -> List[Dict[str, Any]]:
        extension = file_path.suffix.lower()
        if extension == ".txt":
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return [{"page_number": None, "text": self.normalize_text(content)}]
        if extension == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError("pypdf is not installed. Run pip install -r backend/requirements.txt.") from exc

            reader = PdfReader(str(file_path))
            pages = []
            for idx, page in enumerate(reader.pages, start=1):
                text = self.normalize_text(page.extract_text() or "")
                if text:
                    pages.append({"page_number": idx, "text": text})
            return pages
        raise ValueError(f"Unsupported file extension: {extension}")

    def chunk_pages(
        self,
        pages: List[Dict[str, Any]],
        chunk_words: int = CHUNK_WORDS,
        overlap_words: int = CHUNK_OVERLAP_WORDS,
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for page in pages:
            words = page["text"].split()
            if not words:
                continue

            start = 0
            while start < len(words):
                end = start + chunk_words
                chunk_words_list = words[start:end]
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "page_number": page.get("page_number"),
                        "content": " ".join(chunk_words_list),
                    }
                )
                chunk_index += 1
                if start + chunk_words >= len(words):
                    break
                start += max(1, chunk_words - overlap_words)

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
        ollama_client=None,
        limit: int = RETRIEVAL_LIMIT,
    ) -> List[Any]:
        ready_ids = [
            did for did in document_ids
            if (database.get_document(did) or {}).get("status") == "ready"
        ]
        if not ready_ids:
            return []
        return await self.chroma_store.as_retriever(document_ids=ready_ids, k=limit).ainvoke(prompt)

    def delete_document_vectors(self, document_id: int) -> None:
        self.chroma_store.delete_document_vectors(document_id)

    def get_collection(self):
        return self.chroma_store.get_collection()

    def chunk_id(self, document_id: int, chunk_index: int) -> str:
        return f"document-{document_id}-chunk-{chunk_index}"

    def normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def snippet(self, text: str, max_chars: int = 280) -> str:
        normalized = self.normalize_text(text)
        if len(normalized) <= max_chars:
            return normalized
        return f"{normalized[:max_chars].rstrip()}..."
