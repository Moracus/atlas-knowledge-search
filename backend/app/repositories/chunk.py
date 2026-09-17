# app/repositories/chunk.py

from sqlalchemy.orm import Session

from app.db.models import Chunk


class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    async def create_many(self, chunks: list[Chunk]):
        self.db.add_all(chunks)