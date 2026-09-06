import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, BigInteger,ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

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
