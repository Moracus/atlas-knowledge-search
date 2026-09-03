import uuid
from pathlib import Path

from fastapi import UploadFile,HTTPException
from sqlalchemy.orm import Session

from app.db.models import Document
from app.repositories.documents import create_document,get_all_documents,get_document_by_id,delete_document
from uuid import UUID
from app.core.config import settings

STORAGE_DIR = Path(settings.storage_dir)


def save_document(
    db: Session,
    file: UploadFile,
) -> Document:

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
    )

    return create_document(db, document)

def list_documents(db: Session):
    return get_all_documents(db)


def get_document(db:Session,document_id:UUID)->Document|None:
    document = get_document_by_id(db,document_id)
    if document is None :
        raise HTTPException(status_code=404,detail="Document not found")
    return document

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
