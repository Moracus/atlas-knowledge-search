# app/services/chunking/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ChunkData:
    """Pure domain object returned by chunkers."""

    text: str

    file_path: str
    file_name: str
    language: str

    chunk_type: str  # class | function | method | heading | global
    name: str | None

    start_line: int
    end_line: int

    heading_hierarchy: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class BaseChunker(ABC):
    """Every chunker converts one extracted file into semantic chunks."""

    @abstractmethod
    def chunk(
        self,
        text: str,
        file_path: str,
    ) -> list[ChunkData]:
        """
        Convert a single file into structure-aware chunks.

        Args:
            text: Extracted file contents.
            file_path: Relative path (e.g. src/auth/service.py)

        Returns:
            List of ChunkData objects in source order.
        """
        raise NotImplementedError

    @staticmethod
    def detect_language(file_path: str) -> str:
        """Simple extension → language mapping for V0."""
        ext = Path(file_path).suffix.lower()

        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".jsx": "jsx",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".md": "markdown",
            ".txt": "text",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
        }

        return mapping.get(ext, "text")