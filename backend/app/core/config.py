from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ─── App ───────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "AI MediBot v2"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ─── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-random-32-byte-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ─── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://medibot:medibot@db:5432/medibot"

    # ─── LLM Provider ──────────────────────────────────────────────────────────
    # Set one of: "openai" | "huggingface" | "anthropic" | "offline"
    LLM_PROVIDER: Literal["openai", "huggingface", "anthropic", "offline"] = "offline"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.15
    LLM_MAX_TOKENS: int = 512
    LLM_TIMEOUT_SECONDS: int = 30

    # ─── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None  # for OpenAI-compatible endpoints

    # ─── Hugging Face ──────────────────────────────────────────────────────────
    HF_API_TOKEN: Optional[str] = None
    HF_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"

    # ─── Anthropic ─────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: Optional[str] = None

    # ─── RAG / Embeddings ──────────────────────────────────────────────────────
    ENABLE_RAG: bool = True
    RAG_TOP_K: int = 4
    RAG_MIN_SCORE: float = 0.25
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
