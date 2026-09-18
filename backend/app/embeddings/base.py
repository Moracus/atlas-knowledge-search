from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Base interface for all embedding providers.

    Implementations may use local models (Qwen, BGE),
    cloud APIs (OpenAI, Voyage), or anything else.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Embedding vector dimensionality."""
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        Returns:
            List of embedding vectors in the same order as the input.
        """
        pass