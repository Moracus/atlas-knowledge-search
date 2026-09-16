from fastapi import APIRouter, Depends, File, UploadFile,Request
from sqlalchemy.orm import Session

from uuid import UUID
from app.db.dependencies import get_db
from app.schemas.documents import DocumentResponse, uploadResponse
from app.services.documents import save_document,list_documents,remove_document,get_document,service_get_doc_status_by_id
from app.db.models import Document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "", response_model= uploadResponse
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await save_document(db, file,request)

@router.get("", response_model=list[DocumentResponse])
def get_all_documents_route(
    db: Session = Depends(get_db),
):
    return list_documents(db)


@router.get("/{document_id}",status_code = 200,response_model = DocumentResponse)
def get_documents_by_id_route(document_id:UUID,db:Session=Depends(get_db)):
    return get_document(db,document_id)

@router.get("/status/{document_id}",status_code=200)
def get_status(document_id:UUID,db:Session=Depends(get_db)):
    return service_get_doc_status_by_id(db,document_id)

@router.delete("/{document_id}", status_code=204)
def delete_document_route(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    remove_document(db, document_id)