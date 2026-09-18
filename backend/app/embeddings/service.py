from app.embeddings.registry import EmbeddingRegistry


class EmbeddingService:
    """
    High-level API used by ingestion and retrieval.

    The service is provider-agnostic; it simply delegates to the
    configured embedding provider.
    """

    def __init__(self):
        self.provider = EmbeddingRegistry.get_provider()

    @property
    def model_name(self) -> str:
        return self.provider.model_name

    @property
    def dimensions(self) -> int:
        return self.provider.dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        if not texts:
            return []

        return self.provider.embed(texts)

    def embed_text(self, text: str) -> list[float]:
        """Convenience wrapper for a single text."""
        return self.embed_batch([text])[0]