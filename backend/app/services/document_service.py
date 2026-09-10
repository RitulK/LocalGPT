from pathlib import Path

import database
from app.services.runtime import ollama_client, rag_service


def list_documents():
    return database.list_documents()


async def upload_document(file):
    return await rag_service.ingest_upload(file, ollama_client)


def get_document(document_id: int):
    return database.get_document(document_id)


def delete_document(document_id: int) -> bool:
    document = database.delete_document(document_id)
    if not document:
        return False
    rag_service.delete_document_vectors(document_id)
    try:
        Path(document["file_path"]).unlink(missing_ok=True)
    except OSError:
        pass
    return True
