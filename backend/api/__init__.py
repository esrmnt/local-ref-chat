from .chat import router as chat_router
from .knowlwdge import router as upload_router
from .search import router as search_router

__all__ = ["chat_router", "upload_router", "search_router"]
