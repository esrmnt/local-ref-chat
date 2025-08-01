
# DEPRECATED: This file is kept for backward compatibility
# Use backend.settings instead

from backend.settings import settings

# Re-export settings for backward compatibility
ALLOWED_FILE_EXTENSIONS = settings.ALLOWED_FILE_EXTENSIONS
DOCS_FOLDER = settings.DOCS_FOLDER
CHUNK_SIZE_WORDS = settings.CHUNK_SIZE_WORDS
EMBEDDING_MODEL_NAME = settings.EMBEDDING_MODEL_NAME
OLLAMA_API_URL = settings.OLLAMA_API_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
DEFAULT_TOP_K = settings.DEFAULT_TOP_K
