import uuid
from pathlib import Path

from fastapi import UploadFile,HTTPException
from sqlalchemy.orm import Session

from app.db.models import Document,Job
from app.repositories.documents import create_document,get_all_documents,get_document_by_id,delete_document,create_job,get_DocStatus_by_id
from uuid import UUID
from app.core.config import settings

from fastapi import Request

STORAGE_DIR = Path(settings.storage_dir)


async def save_document(
    db: Session,
    file: UploadFile,
    request:Request
) -> Job:

    document_id = uuid.uuid4()

    extension = Path(file.filename or "").suffix

    storage_path = STORAGE_DIR / f"{document_id}{extension}"

    with storage_path.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            output.write(chunk)

    size_bytes = storage_path.stat().st_size

    document = Document(
        id=document_id,
        name=file.filename or "Untitled",
        original_filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        storage_path=str(storage_path),
        relative_path = file.filename or "Untitled"
    )

    create_document(db, document)
    job = service_create_job(db,document_id)
    db.commit()
    await request.app.state.redis.enqueue_job("process_document",str(job.id))

    db.refresh(document)
    db.refresh(job)
    return job

def list_documents(db: Session):
    return get_all_documents(db)


def get_document(db:Session,document_id:UUID)->Document|None:
    document = get_document_by_id(db,document_id)
    if document is None :
        raise HTTPException(status_code=404,detail="Document not found")
    return document

def service_get_doc_status_by_id(db:Session,document_id:UUID):
    status = get_DocStatus_by_id(db,document_id)
    if status is None :
          raise HTTPException(status_code=404,detail="Document not found")
    return status

def remove_document(
    db: Session,
    document_id: UUID,
):
    document = get_document_by_id(db, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    path = Path(document.storage_path)

    if path.exists():
        path.unlink()

    delete_document(db, document)
    db.commit()

def service_create_job(db:Session,document_id:UUID)->Job|None:
    job_id = uuid.uuid4()
    job = Job(id=job_id,
              document_id=document_id,
              )
 
    return create_job(db,job)
    
    
