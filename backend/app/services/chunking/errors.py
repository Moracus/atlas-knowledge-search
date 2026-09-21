class ChunkingError(Exception):
    """Base class for all chunking failures."""


class UnsupportedLanguageError(ChunkingError):
    def __init__(self, file_path: str, language: str | None = None):
        self.file_path = file_path
        self.language = language
        detail = f" (detected: {language})" if language else ""
        super().__init__(f"Unsupported language for '{file_path}'{detail}")


class ChunkerFailedError(ChunkingError):
    def __init__(self, file_path: str, language: str, original: Exception):
        self.file_path = file_path
        self.language = language
        self.original = original
        super().__init__(
            f"{language} chunker failed on '{file_path}': "
            f"{type(original).__name__}: {original}"
        )