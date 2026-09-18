# app/services/chunking/service.py

from app.services.chunking.base import BaseChunker, ChunkData
from app.services.chunking.code.python import PythonChunker
from app.services.chunking.code.javascript import JavaScriptChunker


class ChunkingService:
    def __init__(self):
        self.python = PythonChunker()
        self.javascript = JavaScriptChunker()

    def chunk_file(
        self,
        *,
        text: str,
        file_path: str,
    ) -> list[ChunkData]:

        language = BaseChunker.detect_language(file_path)

        if language == "python":
            return self.python.chunk(text, file_path)

        if language == "javascript":
            return self.javascript.chunk(text, file_path)

        # TODO
        # if language == "markdown":
        #     return self.markdown.chunk(...)

        # TODO
        # return self.fallback.chunk(...)
        return []