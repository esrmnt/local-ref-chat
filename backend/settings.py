import os
from pathlib import Path
from typing import List

class Settings:
    """Application settings with environment variable support."""
    
    # File handling
    ALLOWED_FILE_EXTENSIONS: List[str] = [".pdf", ".txt"]
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Directories
    DOCS_FOLDER: str = os.getenv("DOCS_FOLDER", "docs")
    
    # Chunking
    CHUNK_SIZE_WORDS: int = int(os.getenv("CHUNK_SIZE_WORDS", "500"))
    
    # Embeddings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    
    # Ollama settings
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "30"))
    
    # Search
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    MAX_TOP_K: int = int(os.getenv("MAX_TOP_K", "20"))
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration settings."""
        if cls.CHUNK_SIZE_WORDS <= 0:
            raise ValueError("CHUNK_SIZE_WORDS must be positive")
        
        if cls.MAX_FILE_SIZE_MB <= 0:
            raise ValueError("MAX_FILE_SIZE_MB must be positive")
        
        if cls.DEFAULT_TOP_K <= 0:
            raise ValueError("DEFAULT_TOP_K must be positive")
        
        if cls.MAX_TOP_K < cls.DEFAULT_TOP_K:
            raise ValueError("MAX_TOP_K must be >= DEFAULT_TOP_K")
        
        # Ensure docs folder exists
        Path(cls.DOCS_FOLDER).mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.validate()
