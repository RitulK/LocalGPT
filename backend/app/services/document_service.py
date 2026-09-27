from pathlib import Path

from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import DocumentRepository
from app.services.runtime import ollama_client, rag_service

document_repo = DocumentRepository()


def list_documents():
    with get_connection() as conn:
        return document_repo.list_all(conn)


async def upload_document(file):
    return await rag_service.ingest_upload(file, ollama_client)


def get_document(document_id: int):
    with get_connection() as conn:
        return document_repo.get(conn, document_id)


def delete_document(document_id: int) -> bool:
    with get_connection() as conn:
        document = document_repo.delete(conn, document_id)
        if not document:
            return False
    rag_service.delete_document_vectors(document_id)
    try:
        Path(document["file_path"]).unlink(missing_ok=True)
    except OSError:
        pass
    return True
