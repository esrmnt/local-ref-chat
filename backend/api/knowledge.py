from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from typing import List
import io
import mimetypes

from backend.core.state import doc_manager, indexer
from backend.models import (
    UploadResponse, DocumentListResponse, ErrorResponse, DocumentInfo,
    DocumentContentResponse, DocumentChunksResponse, DocumentChunk
)
from backend.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

async def validate_upload_file(file: UploadFile = File(...)) -> UploadFile:
    """Dependency to validate uploaded files."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    return file

@router.post("/upload", response_model=UploadResponse)
async def upload_files(file: UploadFile = Depends(validate_upload_file)):
    """
    Upload and index a document file.
    
    Supports PDF and TXT files up to the configured size limit.
    """
    try:
        logger.info(f"Processing upload request for file: {file.filename}")
        
        # Save the uploaded file
        file_path, file_size = doc_manager.save_uploaded_file(file)
        
        # Add to index without full rebuild
        try:
            chunks_created = indexer.add_document(doc_manager, file_path)
        except Exception as e:
            # If incremental indexing fails, fall back to full rebuild
            logger.warning(f"Incremental indexing failed, falling back to full rebuild: {e}")
            docs_processed, chunks_created = indexer.rebuild(doc_manager)
        
        response = UploadResponse(
            filename=file.filename,
            message="File uploaded and indexed successfully",
            file_size=file_size,
            chunks_created=chunks_created
        )
        
        logger.info(f"Successfully processed upload: {file.filename} ({chunks_created} chunks)")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper error messages)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred during file upload"
        )

@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """
    List all uploaded documents with detailed information.
    
    Returns a list of documents with metadata including file size, upload date, and chunk count.
    """
    try:
        docs_detailed = doc_manager.list_documents_detailed()
        
        # Convert to DocumentInfo objects
        document_infos = [DocumentInfo(**doc) for doc in docs_detailed]
        
        response = DocumentListResponse(
            documents=document_infos,
            total_count=len(document_infos)
        )
        
        logger.info(f"Listed {len(document_infos)} documents with details")
        return response
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document list"
        )

@router.get("/documents/{filename}/info", response_model=DocumentInfo)
async def get_document_info(filename: str):
    """
    Get detailed information about a specific document.
    
    Args:
        filename: Name of the document
        
    Returns:
        Document metadata including size, type, upload date, and processing stats
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        doc_info = doc_manager.get_document_info(filename)
        
        if doc_info is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Retrieved info for document: {filename}")
        return DocumentInfo(**doc_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document info for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document information"
        )

@router.get("/documents/{filename}/content", response_model=DocumentContentResponse)
async def get_document_content(filename: str):
    """
    Get the full text content of a document.
    
    Args:
        filename: Name of the document
        
    Returns:
        Full extracted text content with metadata
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        content = doc_manager.get_document_content(filename)
        
        if content is None:
            raise HTTPException(status_code=404, detail="Document not found or content could not be extracted")
        
        # Calculate stats
        character_count = len(content)
        word_count = len(content.split())
        file_type = filename.split('.')[-1].lower() if '.' in filename else ''
        
        response = DocumentContentResponse(
            filename=filename,
            content=content,
            file_type=f".{file_type}",
            character_count=character_count,
            word_count=word_count
        )
        
        logger.info(f"Retrieved content for document: {filename} ({character_count} chars)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document content for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document content"
        )

@router.get("/documents/{filename}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(filename: str):
    """
    Get all text chunks for a specific document.
    
    Args:
        filename: Name of the document
        
    Returns:
        List of text chunks with metadata
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        chunks_data = doc_manager.get_document_chunks(filename)
        
        if chunks_data is None:
            raise HTTPException(status_code=404, detail="Document not found or chunks could not be generated")
        
        # Convert to DocumentChunk objects
        chunks = [DocumentChunk(**chunk) for chunk in chunks_data]
        
        response = DocumentChunksResponse(
            filename=filename,
            total_chunks=len(chunks),
            chunks=chunks
        )
        
        logger.info(f"Retrieved {len(chunks)} chunks for document: {filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document chunks for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document chunks"
        )

@router.get("/documents/{filename}/download")
async def download_document(filename: str):
    """
    Download the original document file.
    
    Args:
        filename: Name of the document to download
        
    Returns:
        File download response
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        file_path = doc_manager.docs_folder / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        logger.info(f"Serving download for document: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve download for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download document"
        )

@router.get("/documents/{filename}/preview")
async def preview_document(filename: str, max_chars: int = 1000):
    """
    Get a preview of the document content (first N characters).
    
    Args:
        filename: Name of the document
        max_chars: Maximum number of characters to return (default: 1000)
        
    Returns:
        Document preview with metadata
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        if max_chars <= 0 or max_chars > 10000:
            raise HTTPException(status_code=400, detail="max_chars must be between 1 and 10000")
        
        content = doc_manager.get_document_content(filename)
        
        if content is None:
            raise HTTPException(status_code=404, detail="Document not found or content could not be extracted")
        
        # Create preview
        preview = content[:max_chars]
        is_truncated = len(content) > max_chars
        
        if is_truncated:
            preview += "..."
        
        response = {
            "filename": filename,
            "preview": preview,
            "is_truncated": is_truncated,
            "total_characters": len(content),
            "preview_characters": len(preview)
        }
        
        logger.info(f"Generated preview for document: {filename} ({len(preview)} chars)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate preview for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate document preview"
        )

@router.get("/documents/{filename}/indexed-chunks")
async def get_document_indexed_chunks(filename: str):
    """
    Get all indexed chunks for a specific document (with embeddings).
    
    Args:
        filename: Name of the document
        
    Returns:
        List of indexed chunks with processing metadata
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        chunks = indexer.get_document_chunks_indexed(filename)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="No indexed chunks found for this document")
        
        response = {
            "filename": filename,
            "total_indexed_chunks": len(chunks),
            "chunks": chunks
        }
        
        logger.info(f"Retrieved {len(chunks)} indexed chunks for document: {filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get indexed chunks for {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve indexed chunks"
        )

@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Delete a document and remove it from the index.
    
    Args:
        filename: Name of the document to delete
    """
    try:
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        logger.info(f"Processing delete request for: {filename}")
        
        # Remove from index first
        chunks_removed = indexer.remove_document(filename)
        
        # Remove file from disk
        file_deleted = doc_manager.delete_document(filename)
        
        if not file_deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Successfully deleted document: {filename} ({chunks_removed} chunks removed)")
        
        return JSONResponse(content={
            "message": f"Document '{filename}' deleted successfully",
            "chunks_removed": chunks_removed
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document"
        )

@router.post("/reindex")
async def reindex_documents():
    """
    Rebuild the entire search index from all documents.
    
    This can be useful if the index becomes corrupted or after system updates.
    """
    try:
        logger.info("Starting manual reindex of all documents")
        
        docs_processed, chunks_created = indexer.rebuild(doc_manager)
        
        logger.info(f"Manual reindex completed: {docs_processed} documents, {chunks_created} chunks")
        
        return JSONResponse(content={
            "message": "Reindexing completed successfully",
            "documents_processed": docs_processed,
            "chunks_created": chunks_created
        })
        
    except Exception as e:
        logger.error(f"Manual reindex failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Reindexing failed"
        )
