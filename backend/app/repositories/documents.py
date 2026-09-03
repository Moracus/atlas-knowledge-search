from sqlalchemy.orm import Session
from sqlalchemy import select,desc
from app.db.models import Document
from uuid import UUID

def create_document(
    db: Session,
    document: Document,
) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_all_documents(db: Session) -> list[Document]:
    statement = (
    select(Document)
    .order_by(desc(Document.created_at))
)
    return db.scalars(statement).all()
def get_document_by_id(
    db: Session,
    document_id: UUID,
) -> Document | None:
    statement = select(Document).where(Document.id == document_id)
    return db.scalar(statement)


def delete_document(
    db: Session,
    document: Document,
) -> None:
    db.delete(document)
    db.commit()