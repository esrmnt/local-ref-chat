import requests
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import Field
from typing import Optional

from backend.core.state import indexer
from backend.core.model import get_ollama_answer, check_ollama_health
from backend.models import ChatRequest, ChatResponse, SearchResult, ErrorResponse
from backend.settings import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/ask", response_model=ChatResponse)
def ask_question(
    q: str = Query(
        ..., 
        description='Your natural language question',
        min_length=1,
        max_length=1000
    ),
    top_k: int = Query(
        default=settings.DEFAULT_TOP_K,
        description="Number of relevant chunks to retrieve for context",
        ge=1,
        le=settings.MAX_TOP_K
    )
):
    """
    Ask a question about your documents using RAG (Retrieval-Augmented Generation).
    
    The system will:
    1. Find the most relevant document chunks for your question
    2. Send them as context to the local LLM (Ollama)
    3. Generate an answer based on your documents
    
    Args:
        q: Your natural language question
        top_k: Number of relevant document chunks to use as context
        
    Returns:
        AI-generated answer with source citations
    """
    try:
        logger.info(f"Processing question: '{q}' (top_k={top_k})")
        
        # Check if Ollama is available
        if not check_ollama_health():
            raise HTTPException(
                status_code=503,
                detail="Ollama service is not available. Please ensure Ollama is running."
            )
        
        # Retrieve most relevant chunks for context
        chunks = indexer.semantic_search(q, top_k)
        
        if not chunks:
            logger.warning(f"No relevant context found for question: '{q}'")
            return ChatResponse(
                answer="I couldn't find any relevant information in your documents to answer this question. Please try rephrasing your question or upload more documents.",
                context=[],
                question=q
            )
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks for question")
        
        # Prepare context text
        context_text = "\n\n".join([
            f"Source {i+1}: {chunk['text_snippet']}"
            for i, chunk in enumerate(chunks)
        ])
        
        # Create a well-structured prompt
        prompt = f"""You are a helpful assistant that answers questions based on provided document context. Use only the information from the context below to answer the question. If the context doesn't contain enough information to fully answer the question, say so explicitly.

Context from documents:
{context_text}

Question: {q}

Instructions:
- Answer based only on the provided context
- Be concise but comprehensive
- If the context is insufficient, acknowledge this limitation
- Do not make assumptions or add information not in the context

Answer:"""

        try:
            # Send the prompt to Ollama and get the response
            logger.info("Sending request to Ollama for answer generation")
            result = get_ollama_answer(prompt=prompt, stream=False)
            
            answer = result.get("response", "").strip()
            
            if not answer:
                logger.warning("Empty response received from Ollama")
                answer = "I apologize, but I wasn't able to generate a proper response. Please try asking your question differently."
            
            # Convert chunks to SearchResult objects
            context_results = [SearchResult(**chunk) for chunk in chunks]
            
            response = ChatResponse(
                answer=answer,
                context=context_results,
                question=q
            )
            
            logger.info(f"Successfully generated answer for question: '{q}'")
            return response
            
        except requests.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise HTTPException(
                status_code=503,
                detail="Failed to get response from Ollama. Please check if Ollama is running and try again."
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing question '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your question"
        )

@router.post("/ask", response_model=ChatResponse)
def ask_question_post(request: ChatRequest):
    """
    Ask a question about your documents using POST method (alternative to GET).
    
    This endpoint accepts the same parameters as the GET version but via POST body,
    which can be useful for longer questions or when integrating with web applications.
    """
    return ask_question(q=request.question, top_k=request.top_k)

@router.get("/ollama/status")
def check_ollama_status():
    """
    Check the status of the Ollama service.
    
    Returns information about whether Ollama is available and ready to process requests.
    """
    try:
        is_available = check_ollama_health()
        
        return {
            "available": is_available,
            "service": "Ollama",
            "url": settings.OLLAMA_API_URL,
            "model": settings.OLLAMA_MODEL,
            "status": "healthy" if is_available else "unavailable"
        }
        
    except Exception as e:
        logger.error(f"Failed to check Ollama status: {e}")
        return {
            "available": False,
            "service": "Ollama",
            "url": settings.OLLAMA_API_URL,
            "model": settings.OLLAMA_MODEL,
            "status": "error",
            "error": str(e)
        }
