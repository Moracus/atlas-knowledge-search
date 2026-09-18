# app/workers/tasks.py

import uuid
import logging

from app.db.database import SessionLocal
from app.db.models import JobStatus, DocumentStatus
from app.repositories.documents import (
    get_job_by_id,
    get_document_by_id,
)
from app.application.ingest import IngestApplication

logger = logging.getLogger(__name__)


async def process_document(ctx, job_id: str):
    db = SessionLocal()

    job = None
    document = None

    try:
        # Load job + document
        job = get_job_by_id(db, uuid.UUID(job_id))
        if job is None:
            return

        document = get_document_by_id(db, job.document_id)
        if document is None:
            return

        # Update job state
        job.status = JobStatus.processing
        job.progress = 10
        db.commit()

        # Run shared ingestion pipeline
        app = IngestApplication(db)
        await app.ingest_existing_document(document)

        # Finalize job
        job.progress = 100
        job.status = JobStatus.completed
        db.commit()

    except Exception as e:
        db.rollback()

        if job:
            job.status = JobStatus.failed
            job.error_message = str(e)[:1000]

        if document:
            document.status = DocumentStatus.failed

        db.commit()
        logger.exception(e)

    finally:
        db.close()