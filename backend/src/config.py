from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = str(os.getenv("OLLAMA_BASE_URL", "http://ollama-generation:11434"))
    agent_model: str = str(os.getenv("AGENT_MODEL", "qwen3:1.7b"))

    ollama_judge_url: str = str(os.getenv("OLLAMA_JUDGE_URL", "http://ollama-judge:11434"))
    judge_model: str = str(os.getenv("JUDGE_MODEL", "deepseek-r1:1.5b"))

    ollama_embed_url: str = str(os.getenv("OLLAMA_EMBED_URL", "http://ollama-embed:11434"))
    embedding_model: str = str(os.getenv("EMBEDDING_MODEL", "nomic-embed-text"))

    chroma_db_path: str = str(os.getenv("CHROMA_DB_PATH", "data/chroma_db"))
    chroma_collection: str = str(os.getenv("CHROMA_COLLECTION", "reviews"))
    chroma_items_collection: str = str(os.getenv("CHROMA_ITEMS_COLLECTION", "items"))
    chroma_user_reviews_collection: str = str(os.getenv("CHROMA_USER_REVIEWS_COLLECTION", "user_reviews"))

    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", 10))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", 0.7))   # type: ignore
    llm_top_p: float = float(os.getenv("LLM_TOP_P", 0.8))   # type: ignore
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", 512))
    log_level: str = str(os.getenv("LOG_LEVEL", "INFO"))

    database_url: str = str(os.getenv("DATABASE_URL", "sqlite:///data/jollof.db"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
