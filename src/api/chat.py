import requests
from src.core.state import indexer 
from fastapi import APIRouter, Query
from src.config import OLLAMA_API_URL, OLLAMA_MODEL

router = APIRouter()

OLLAMA_URL = OLLAMA_API_URL 
OLLAMA_MODEL = OLLAMA_MODEL 

@router.get("/ask")
def ask(question: str = Query(..., description='Your natural language question'), top_k: int = 5):
    # Retrieve most relevant chunks for context
    chunks = indexer.semantic_search(question, top_k=top_k)
    context_text = "\n\n".join([chunk["text_snippet"] for chunk in chunks])
    prompt = f"Use the following context from my private notes to answer the question as thoroughly as possible.\n\nContext:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,  # disable streaming
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        # Ollama streams responses by default; to keep it simple, just return the whole response here
        return {"answer": result.get("response", "No response"), "context": chunks}
    except Exception as e:
        return {"error": str(e)}
