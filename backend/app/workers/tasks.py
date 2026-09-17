import uuid
import logging

from app.db.database import SessionLocal
from app.db.models import JobStatus, DocumentStatus,Chunk,Document
from app.repositories.documents import (
    get_job_by_id,
    get_document_by_id
)
from app.repositories.chunk import ChunkRepository
from app.services.ingestion.service import IngestionService,ExtractionResult
from app.services.chunking.service import ChunkingService

logger = logging.getLogger(__name__)

async def process_document(ctx, job_id: str):
    db = SessionLocal()

    job = None
    doc = None

    try:
        job = get_job_by_id(db, uuid.UUID(job_id))
        if not job:
            return

        doc:Document = get_document_by_id(db, job.document_id)
        if not doc:
            return

        job.status = JobStatus.processing
        doc.status = DocumentStatus.processing
        job.progress = 10
        db.commit()

        ingestion = IngestionService()

        result:ExtractionResult = await ingestion.ingest(file_path=doc.storage_path,document_id=doc.id)
        doc.extracted_path = result.path
        # chunking
        chunk_service = ChunkingService()
        chunk_repo = ChunkRepository(db)

        chunks = chunk_service.chunk_file(
            text= result.text,
            file_path=doc.storage_path
        )

        chunk_models = [
            Chunk(
                document_id=doc.id,
                chunk_index=index,

                text=chunk.text,

                file_path=chunk.file_path,
                file_name=chunk.file_name,
                language=chunk.language,

                chunk_type=chunk.chunk_type,
                name=chunk.name,

                start_line=chunk.start_line,
                end_line=chunk.end_line,

                heading_hierarchy=chunk.heading_hierarchy,
                dependencies=chunk.dependencies,
            )
            for index, chunk in enumerate(chunks)
        ]
        await chunk_repo.create_many(chunk_models)
        

        job.progress = 100
        job.status = JobStatus.completed
        doc.status = DocumentStatus.ready

        db.commit()

    except Exception as e:
        db.rollback()

        if job:
            job.status = JobStatus.failed
            job.error_message = f"{type(e).__name__}: {e.orig}"

        if doc:
            doc.status = DocumentStatus.failed

        db.commit()

        logger.exception(e)

    finally:
        db.close()