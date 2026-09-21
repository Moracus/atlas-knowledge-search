# app/application/ingest.py

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, DocumentStatus
from app.repositories.documents import create_document
from app.repositories.chunk import ChunkRepository
from app.services.chunking.service import ChunkingService
from app.services.ingestion.service import IngestionService
from app.core.paths import CONFIG_DIR

UPLOAD_DIR = Path(f"{CONFIG_DIR}/storage/uploads")


class IngestApplication:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService()
        self.chunking = ChunkingService()
        self.chunk_repo = ChunkRepository(db)

    # ------------------------------------------------------------------
    # CLI ENTRYPOINT
    # ------------------------------------------------------------------
    async def ingest_local_file(
        self,
        *,
        absolute_path: Path,
        relative_path: str,
        repo_name: str | None = None,
        session_id: str | None = None,
    ) -> list[Chunk]:          # was -> Document, but you return chunks
        document_id = uuid.uuid4()
        extension = absolute_path.suffix

        storage_path = UPLOAD_DIR / f"{document_id}{extension}"
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(absolute_path, storage_path)

        try:
            document = Document(
                id=document_id,
                name=absolute_path.name,
                original_filename=absolute_path.name,
                content_type="text/plain",
                size_bytes=storage_path.stat().st_size,
                storage_path=str(storage_path),
                relative_path=relative_path,
                repo_name=repo_name,
                status=DocumentStatus.processing,
                session_id=session_id,
            )

            create_document(self.db, document)
            self.db.flush()

            chunks = await self._run_pipeline(document)

            self.db.commit()
            self.db.refresh(document)
            return chunks
        except Exception:
            # the CLI's db.rollback() removes the Document row,
            # but not the file we copied, so clean it up here
            storage_path.unlink(missing_ok=True)
            raise
    # ------------------------------------------------------------------
    # WORKER ENTRYPOINT
    # ------------------------------------------------------------------
    async def ingest_existing_document(
        self,
        document: Document,
    ) -> Document:
        """
        Used by ARQ worker.

        Assumes the Document row and uploaded file already exist.
        """

        document.status = DocumentStatus.processing

        await self._run_pipeline(document)

        self.db.commit()
        self.db.refresh(document)

        return document

    # ------------------------------------------------------------------
    # SHARED PIPELINE
    # ------------------------------------------------------------------
    async def _run_pipeline(self, document: Document) -> None:
        """
        Shared ingestion logic used by both CLI and Worker.
        """

        result = await self.ingestion.ingest(
            file_path=document.storage_path,
            document_id=document.id,
        )

        document.extracted_path = result.path

        chunks = self.chunking.chunk_file(
            text=result.text,
            file_path=document.relative_path,  # preserve repo path
        )

        chunk_models = [
            Chunk(
                document_id=document.id,
                chunk_index=index,
                text=chunk.text,
                file_path=document.relative_path,
                file_name=chunk.file_name,
                repo_name=document.repo_name,
                language=chunk.language,
                chunk_type=chunk.chunk_type,
                name=chunk.name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                heading_hierarchy=chunk.heading_hierarchy,
                dependencies=chunk.dependencies,
                embedding_status="pending",
                summary_status="pending",
            )
            for index, chunk in enumerate(chunks)
        ]

        await self.chunk_repo.create_many(chunk_models)


        document.status = DocumentStatus.ready
        return chunk_models