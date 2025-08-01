from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SearchResult(BaseModel):
    """Model for search result items."""
    filename: str = Field(..., description="Source document filename")
    chunk_index: int = Field(..., description="Index of the chunk within the document")
    text_snippet: str = Field(..., description="Preview of the text content")
    citation: str = Field(..., description="Formatted citation for the result")
    similarity: Optional[float] = Field(None, description="Similarity score for semantic search")

class SearchResponse(BaseModel):
    """Model for search API responses."""
    results: List[SearchResult] = Field(..., description="List of search results")
    query: str = Field(..., description="The original search query")
    total_results: int = Field(..., description="Total number of results found")

class UploadResponse(BaseModel):
    """Model for file upload responses."""
    filename: str = Field(..., description="Name of the uploaded file")
    message: str = Field(..., description="Status message")
    file_size: Optional[int] = Field(None, description="Size of uploaded file in bytes")
    chunks_created: Optional[int] = Field(None, description="Number of chunks created from the document")

class DocumentInfo(BaseModel):
    """Model for document information."""
    filename: str = Field(..., description="Document filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File extension")
    upload_date: Optional[datetime] = Field(None, description="When the file was uploaded")
    chunks_count: int = Field(..., description="Number of text chunks created from this document")
    character_count: Optional[int] = Field(None, description="Total characters in the document")

class DocumentListResponse(BaseModel):
    """Model for document list responses."""
    documents: List[DocumentInfo] = Field(..., description="List of document information")
    total_count: int = Field(..., description="Total number of documents")

class DocumentContentResponse(BaseModel):
    """Model for document content responses."""
    filename: str = Field(..., description="Document filename")
    content: str = Field(..., description="Full text content of the document")
    file_type: str = Field(..., description="File extension")
    character_count: int = Field(..., description="Total characters in the document")
    word_count: int = Field(..., description="Estimated word count")

class DocumentChunk(BaseModel):
    """Model for document text chunks."""
    chunk_index: int = Field(..., description="Index of this chunk within the document")
    text: str = Field(..., description="Text content of the chunk")
    word_count: int = Field(..., description="Number of words in this chunk")
    character_count: int = Field(..., description="Number of characters in this chunk")

class DocumentChunksResponse(BaseModel):
    """Model for document chunks response."""
    filename: str = Field(..., description="Document filename")
    total_chunks: int = Field(..., description="Total number of chunks")
    chunks: List[DocumentChunk] = Field(..., description="List of text chunks")

class ChatRequest(BaseModel):
    """Model for chat/ask requests."""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of relevant chunks to retrieve")

class ChatResponse(BaseModel):
    """Model for chat/ask responses."""
    answer: str = Field(..., description="AI-generated answer")
    context: List[SearchResult] = Field(..., description="Source context used for the answer")
    question: str = Field(..., description="The original question")

class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")

class HealthResponse(BaseModel):
    """Model for health check responses."""
    status: str = Field(..., description="Service status")
    version: Optional[str] = Field(None, description="Application version")
    ollama_available: bool = Field(..., description="Whether Ollama service is available")
    documents_count: int = Field(..., description="Number of indexed documents")
    chunks_count: int = Field(..., description="Number of indexed chunks")
