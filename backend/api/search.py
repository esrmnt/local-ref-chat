from fastapi import APIRouter, Query
from backend.core.state import indexer

router = APIRouter()

@router.get("/search")
def search_docs(q: str = Query(..., description="Search keyword")):
    results = indexer.keyword_search(q)
    return {"results": results}

@router.get("/semantic_search")
def semantic_search(q: str = Query(..., description="Semantic search query"), top_k: int = 5):
    results = indexer.semantic_search(q, top_k=top_k)
    return {"results": results}
