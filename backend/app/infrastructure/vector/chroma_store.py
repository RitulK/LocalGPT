from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever


class ChromaStore:
    """Manages persistent Chroma vector store and exposes filtered LangChain retrievers."""

    def __init__(
        self,
        chroma_dir: Optional[Path] = None,
        collection_name: str = "localgpt_documents",
        embedding_function: Optional[Any] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.chroma_dir = chroma_dir or (base_dir / "chroma")
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._vector_store = Chroma(
            client=self._client,
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
        )

    def get_collection(self):
        return self._collection

    def as_retriever(
        self, document_ids: Optional[List[int]] = None, k: int = 5
    ) -> BaseRetriever:
        search_kwargs: Dict[str, Any] = {"k": k}
        if document_ids:
            if len(document_ids) == 1:
                search_kwargs["filter"] = {"document_id": document_ids[0]}
            else:
                search_kwargs["filter"] = {"document_id": {"$in": document_ids}}

        return self._vector_store.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )

    def delete_document_vectors(self, document_id: int) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception:
            pass
