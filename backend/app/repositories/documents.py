from sqlalchemy.orm import Session

from app.db.models import Document


def create_document(
    db: Session,
    document: Document,
) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)

    return document