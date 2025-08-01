from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from backend.core.state import indexer
from backend.models import SearchResponse, SearchResult
from backend.settings import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/search", response_model=SearchResponse)
def search_docs(
    q: str = Query(..., description="Search keyword", min_length=1, max_length=500),
    case_sensitive: bool = Query(False, description="Whether to perform case-sensitive search")
):
    """
    Perform keyword search across all indexed documents.
    
    Args:
        q: Search query string
        case_sensitive: Whether to perform case-sensitive matching
        
    Returns:
        Search results with text snippets and citations
    """
    try:
        logger.info(f"Performing keyword search for: '{q}' (case_sensitive={case_sensitive})")
        
        results = indexer.keyword_search(q, case_sensitive=case_sensitive)
        
        # Convert to response model
        search_results = [SearchResult(**result) for result in results]
        
        response = SearchResponse(
            results=search_results,
            query=q,
            total_results=len(search_results)
        )
        
        logger.info(f"Keyword search returned {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Keyword search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Search operation failed"
        )

@router.get("/semantic_search", response_model=SearchResponse)
def semantic_search(
    q: str = Query(..., description="Semantic search query", min_length=1, max_length=500),
    top_k: int = Query(
        default=settings.DEFAULT_TOP_K,
        description="Number of top results to return",
        ge=1,
        le=settings.MAX_TOP_K
    )
):
    """
    Perform semantic search using AI embeddings across all indexed documents.
    
    Args:
        q: Search query string
        top_k: Number of most relevant results to return
        
    Returns:
        Search results ranked by semantic similarity with similarity scores
    """
    try:
        logger.info(f"Performing semantic search for: '{q}' (top_k={top_k})")
        
        results = indexer.semantic_search(q, top_k=top_k)
        
        # Convert to response model
        search_results = [SearchResult(**result) for result in results]
        
        response = SearchResponse(
            results=search_results,
            query=q,
            total_results=len(search_results)
        )
        
        logger.info(f"Semantic search returned {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Semantic search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Semantic search operation failed"
        )

@router.get("/search/stats")
def get_search_stats():
    """
    Get statistics about the search index.
    
    Returns information about indexed documents and chunks.
    """
    try:
        stats = indexer.get_stats()
        
        logger.info("Retrieved search index statistics")
        return {
            "message": "Search index statistics",
            **stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve search statistics"
        )
