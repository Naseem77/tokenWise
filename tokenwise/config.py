"""Configuration management for TokenWise."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Application Settings
    debug: bool = True
    log_level: str = "INFO"
    
    # Vector Database
    chroma_persist_directory: str = "./chroma_db"
    
    # Optimization Settings
    default_token_budget: int = 4000
    cache_ttl: int = 3600
    
    # Scoring Weights
    embedding_weight: float = 0.5
    keyword_weight: float = 0.2
    recency_weight: float = 0.15
    relationship_weight: float = 0.1
    llm_weight: float = 0.05
    
    # Chunking Settings
    default_chunk_size: int = 512
    chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

