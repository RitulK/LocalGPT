from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import document_service

router = APIRouter()


@router.get("/documents")
async def list_documents():
    return {"documents": document_service.list_documents()}


@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    try:
        return {"document": await document_service.upload_document(file)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {exc}")


@router.get("/documents/{document_id}")
async def get_document(document_id: int):
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document": document}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    if not document_service.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted"}
