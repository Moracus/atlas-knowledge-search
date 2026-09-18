import enum
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, String, BigInteger,ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.config import settings
from app.db.database import Base


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"

class JobStatus(str,enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class ProcessingStatus(str,enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(255))

    original_filename: Mapped[str] = mapped_column(
        String(255)
    )
    extracted_path: Mapped[str | None] # plain text
    relative_path: Mapped[str | None]
    repo_name :Mapped[str | None]
    content_type: Mapped[str] = mapped_column(
        String(100)
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger
    )

    storage_path: Mapped[str] = mapped_column(
        String(500)
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        default="upload",
    )

    status: Mapped[DocumentStatus] = mapped_column(
    Enum(DocumentStatus),
    default=DocumentStatus.uploaded,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Job(Base):
    __tablename__ = "jobs"
    id : Mapped[uuid.UUID] = mapped_column(primary_key="true",default = uuid.uuid4)
    document_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    status : Mapped[JobStatus] = mapped_column(Enum(JobStatus),default= JobStatus.queued)
    progress: Mapped[int] = mapped_column(
    default=0)
    error_message : Mapped[str|None] = mapped_column(String(1000),default=None)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now()) 



class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[str] = mapped_column(nullable=False)

    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    repo_name: Mapped[str | None] = mapped_column(String, nullable=True)

    language: Mapped[str] = mapped_column(String, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String, nullable=False)

    name: Mapped[str | None] = mapped_column(String, nullable=True)

    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)

    embedding: Mapped[list[float]] = mapped_column(
    Vector(settings.EMBEDDING_DIMENSIONS),
    nullable=True,
)

    heading_hierarchy: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    dependencies: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(nullable=True)

    embedding_status : Mapped[ProcessingStatus]= mapped_column(
       Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.pending,
        server_default="pending",
    )

    summary_status : Mapped[ProcessingStatus]= mapped_column(
       Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.pending,
        server_default="pending",
    )

    

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )