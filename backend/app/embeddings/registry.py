from app.core.config import settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.qwen import QwenProvider


class EmbeddingRegistry:
    """Factory + singleton cache for embedding providers."""

    _provider: EmbeddingProvider | None = None

    @classmethod
    def get_provider(cls) -> EmbeddingProvider:
        # Return cached instance if already loaded
        if cls._provider is not None:
            return cls._provider

        provider_name = settings.EMBEDDING_PROVIDER.lower()

        if provider_name == "qwen":
            cls._provider = QwenProvider(
                model_name=settings.EMBEDDING_MODEL
            )
            return cls._provider

        raise ValueError(f"Unsupported embedding provider: {provider_name}")

    @classmethod
    def reset(cls) -> None:
        """
        Clear the cached provider.

        Useful for tests or when switching models.
        """
        cls._provider = None