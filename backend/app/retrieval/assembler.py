# app/retrieval/assembler.py

from __future__ import annotations

from dataclasses import dataclass

from app.db.models import Chunk
from app.llm.base import Message
from app.llm.prompts import build_messages


@dataclass(slots=True)
class Source:
    id: int
    file_path: str
    start_line: int
    end_line: int


class ContextAssembler:
    """
    Converts retrieved chunks into LLM-ready messages and structured citations.
    """

    def __init__(
        self,
        max_chunks: int = 8,
        max_characters: int = 18_000,
    ) -> None:
        self.max_chunks = max_chunks
        self.max_characters = max_characters

    def build(
        self,
        question: str,
        chunks: list[Chunk],
    ) -> tuple[list[Message], list[Source]]:
        selected = self._select_chunks(chunks)

        messages = build_messages(question, selected)

        sources = [
            Source(
                id=i,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
            )
            for i, chunk in enumerate(selected, start=1)
        ]

        return messages, sources

    def _select_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Keep chunks in retrieval order while respecting size limits.
        """
        selected: list[Chunk] = []
        total_chars = 0

        for chunk in chunks:
            if len(selected) >= self.max_chunks:
                break

            chunk_size = len(chunk.text)

            if total_chars + chunk_size > self.max_characters:
                break

            selected.append(chunk)
            total_chars += chunk_size

        return selected