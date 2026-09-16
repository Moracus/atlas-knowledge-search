import uuid
import logging

from app.db.database import SessionLocal
from app.db.models import JobStatus, DocumentStatus
from app.repositories.documents import (
    get_job_by_id,
    get_document_by_id
)
from app.services.ingestion import IngestionService

logger = logging.getLogger(__name__)

async def process_document(ctx, job_id: str):
    db = SessionLocal()

    job = None
    doc = None

    try:
        job = get_job_by_id(db, uuid.UUID(job_id))
        if not job:
            return

        doc = get_document_by_id(db, job.document_id)
        if not doc:
            return

        job.status = JobStatus.processing
        doc.status = DocumentStatus.processing
        job.progress = 10
        db.commit()

        ingestion = IngestionService()

        result = await ingestion.ingest(file_path=doc.storage_path,document_id=doc.id)

        # logger.info(f"Extracted {len(text)} characters")
        doc.extracted_path = result.path

        job.progress = 100
        job.status = JobStatus.completed
        doc.status = DocumentStatus.ready

        db.commit()

    except Exception as e:
        db.rollback()

        if job:
            job.status = JobStatus.failed
            job.error_message = str(e)

        if doc:
            doc.status = DocumentStatus.failed

        db.commit()

        logger.exception(e)

    finally:
        db.close()