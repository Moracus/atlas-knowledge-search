from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk
from app.embeddings.service import EmbeddingService


class VectorSearchService:
    def __init__(self, db: Session,embeddings: EmbeddingService,):
        self.db = db
        self.embeddings = embeddings

    def search(self, query: str, k: int = 5) -> list[Chunk]:
        """
        Return the top-k most semantically similar chunks.
        """
        query_vector = self.embeddings.embed_text(query)

        stmt = (
            select(Chunk)
            .order_by(Chunk.embedding.cosine_distance(query_vector))
            .limit(k)
        )

        return list(self.db.scalars(stmt).all())