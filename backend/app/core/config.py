from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import CONFIG_DIR, CONFIG_FILE


class Settings(BaseSettings):
    database_url: str
    redis_host: str
    storage_dir: str = str(CONFIG_DIR / "storage")
    EMBEDDING_PROVIDER: str = "qwen"
    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"
    EMBEDDING_DIMENSIONS: int = 1024
    OPENROUTER_API_KEY :str
    OPENAI_API_KEY :str
    LLM_PROVIDER :str = "openai"

    model_config = SettingsConfigDict(env_file=CONFIG_FILE, extra="ignore")


settings = Settings()