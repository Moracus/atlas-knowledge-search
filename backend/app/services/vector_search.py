from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models import Chunk
from app.embeddings.service import EmbeddingService
from app.db.models import Chunk, Document

class VectorSearchService:
    def __init__(self, db: Session,embeddings: EmbeddingService,):
        self.db = db
        self.embeddings = embeddings

    def search(
        self,
        query: str,
        session_id: UUID,
        k: int = 5,
    ) -> list[Chunk]:

        query_vector = self.embeddings.embed_text(query)

        stmt = (
            select(Chunk)
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.session_id == session_id)
            .order_by(Chunk.embedding.cosine_distance(query_vector))
            .limit(k)
        )

        return list(self.db.scalars(stmt).all())