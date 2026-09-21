from app.llm.openai import OpenAIProvider
from app.llm.base import LLMProvider
from app.llm.openrouter import OpenRouterProvider
from app.core.config import settings

def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        return OpenAIProvider()

    if provider == "openrouter":
        return OpenRouterProvider()

    raise ValueError(f"Unsupported LLM provider: {provider}")