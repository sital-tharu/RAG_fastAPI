from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Financial RAG API"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str
    
    # Google Gemini
    GOOGLE_API_KEY: str

    # Groq

    groq_api_key: str
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "chroma"
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    
    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
