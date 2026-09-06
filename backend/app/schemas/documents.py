from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    content_type: str
    size_bytes: int
    source_type: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class uploadResponse(BaseModel):
    document_id:UUID
    id : UUID
    status : str

    model_config = ConfigDict(from_attributes=True)
