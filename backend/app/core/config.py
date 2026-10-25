import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "TripQuery AI"
    API_PREFIX: str = "/api"
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = ""
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None
    
    # RAG Settings
    TOP_K: int = 5
    RELEVANCE_THRESHOLD: float = 0.45
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    USE_SENTENCE_TRANSFORMERS: bool = True
    
    # Database & Storage
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'tripquery.db'}"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    VECTOR_STORE_DIR: Path = BASE_DIR / "data" / "vector_store"
    MAX_FILE_SIZE_MB: int = 20
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure required directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
