import nltk
import threading
from fastapi import FastAPI
from src.api import upload, search, chat  # import api routers
from src.core.state import doc_manager, indexer

nltk.download("punkt")
nltk.download("punkt_tab")

app = FastAPI()

# Include routers from api
app.include_router(upload.router)
app.include_router(search.router)
app.include_router(chat.router)

# Startup indexing
def startup_index():
    if doc_manager.docs_folder.exists():
        print("Indexing documents at startup...")
        indexer.rebuild(doc_manager)
        print("Startup indexing done.")

threading.Thread(target=startup_index).start()