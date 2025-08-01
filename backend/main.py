import nltk
import threading
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import knowledge, search, chat
from backend.core.state import doc_manager, indexer
from backend.logging_config import setup_logging, get_logger
from backend.settings import settings
from backend.models import ErrorResponse, HealthResponse

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Download NLTK data with error handling
def download_nltk_data():
    """Download required NLTK data with error handling."""
    try:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download NLTK data: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting Reference Chat application...")
    
    try:
        # Download NLTK data
        download_nltk_data()
        
        # Start background indexing
        startup_task = asyncio.create_task(startup_index_async())
        await startup_task
        
        logger.info("Application startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down application...")

async def startup_index_async():
    """Asynchronous startup indexing with error handling."""
    try:
        if doc_manager.docs_folder.exists():
            logger.info("Starting document indexing at startup...")
            
            # Run indexing in a thread to avoid blocking
            def index_documents():
                try:
                    indexer.rebuild(doc_manager)
                    logger.info("Startup indexing completed successfully")
                except Exception as e:
                    logger.error(f"Indexing failed during startup: {e}")
            
            thread = threading.Thread(target=index_documents, daemon=True)
            thread.start()
            
        else:
            logger.info("No documents folder found, skipping startup indexing")
            
    except Exception as e:
        logger.error(f"Failed to start indexing: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Reference Chat API",
    description="API for local search and RAG chat assistant for your documents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # CORS is added, but is highly permissive. Can be added with specific details for usages in production.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else "An unexpected error occurred"
        ).dict()
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check Ollama availability
        ollama_available = True
        try:
            from backend.core.model import check_ollama_health
            ollama_available = check_ollama_health()
        except Exception:
            ollama_available = False
        
        return HealthResponse(
            status="healthy",
            ollama_available=ollama_available,
            documents_count=len(doc_manager.list_documents()),
            chunks_count=len(indexer.index)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# Include routers from api
app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )