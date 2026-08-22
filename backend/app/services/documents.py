import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.models import Document
from app.repositories.documents import create_document


STORAGE_DIR = Path("storage")


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