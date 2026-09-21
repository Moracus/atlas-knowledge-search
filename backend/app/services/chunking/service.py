from app.services.chunking.base import BaseChunker, ChunkData
from app.services.chunking.code.python import PythonChunker
from app.services.chunking.code.javascript import JavaScriptChunker
from app.services.chunking.errors import (
    ChunkingError,
    ChunkerFailedError,
    UnsupportedLanguageError,
)


class ChunkingService:
    def __init__(self):
        self._chunkers: dict[str, BaseChunker] = {
            "python": PythonChunker(),
            "javascript": JavaScriptChunker(),
            # "markdown": MarkdownChunker(),  # TODO
        }

    def chunk_file(self, *, text: str, file_path: str) -> list[ChunkData]:
        language = BaseChunker.detect_language(file_path)
        chunker = self._chunkers.get(language)

        if chunker is None:
            raise UnsupportedLanguageError(file_path, language)

        try:
            return chunker.chunk(text, file_path)
        except ChunkingError:
            raise
        except Exception as e:
            raise ChunkerFailedError(file_path, language, e) from e