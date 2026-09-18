from sentence_transformers import SentenceTransformer

from app.embeddings.base import EmbeddingProvider


class QwenProvider(EmbeddingProvider):
    """
    Local embedding provider using Qwen3-Embedding-0.6B.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
    ):
        self._model_name = model_name
        self._model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
        )

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embeddings.tolist()