import requests
from src.core.state import indexer
from fastapi import APIRouter, Query
from src.core import get_ollama_answer
from src.config import OLLAMA_API_URL, OLLAMA_MODEL

router = APIRouter()

OLLAMA_URL = OLLAMA_API_URL 
OLLAMA_MODEL = OLLAMA_MODEL 

@router.get("/ask")
def ask(q: str = Query(..., description='Your natural language question')):
    # Retrieve most relevant chunks for context
    chunks = indexer.semantic_search(q, 5)
    print(f"Retrieved {len(chunks)} relevant chunks for question: {q}")
    context_text = "\n\n".join([chunk["text_snippet"] for chunk in chunks])
    prompt = f"Use the following context from my private notes to answer the question as thoroughly as possible.\n\nContext:\n{context_text}\n\nQuestion: {q}\n\nAnswer:"

    try:
        # Send the prompt to Ollama and get the response
        result = get_ollama_answer(prompt=prompt, stream=False)
        # Ollama streams responses by default; to keep it simple, just return the whole response here
        return {"answer": result.get("response", "No response"), "context": chunks}
    except Exception as e:
        return {"error": str(e)}
