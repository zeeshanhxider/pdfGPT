from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # App settings
    app_name: str = "PDF ChatBot RAG"
    debug: bool = False
    version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf"]
    upload_dir: str = "./uploads"
    
    # ChromaDB settings
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "pdf_documents"
    
    # Embedding model settings
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"  # Change to "cuda" if GPU available
    
    # LLM settings
    use_local_llm: bool = False  # Prefer external APIs for better quality
    local_llm_model_name: str = "microsoft/DialoGPT-medium"
    
    # External API settings (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    
    # Text processing settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens_per_chunk: int = 512
    
    # Retrieval settings
    retrieval_k: int = 5  # Number of chunks to retrieve
    similarity_threshold: float = 0.1  # Very low threshold for testing
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()
