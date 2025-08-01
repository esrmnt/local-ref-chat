import shutil
import mimetypes
from pathlib import Path
from typing import List, BinaryIO, Optional, Dict, Any
from datetime import datetime
from PyPDF2 import PdfReader
from nltk.tokenize import sent_tokenize
from fastapi import UploadFile, HTTPException

from backend.settings import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)

class DocumentManager:
    """Manages document storage, text extraction, and chunking."""
    
    def __init__(self, docs_folder: str = None):
        self.docs_folder = Path(docs_folder or settings.DOCS_FOLDER)
        self.docs_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"DocumentManager initialized with folder: {self.docs_folder}")

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file for security and format requirements."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
            )
        
        # Check file size
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size_bytes:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
                )
        
        # Validate MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        valid_mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain'
        }
        
        expected_mime = valid_mime_types.get(file_ext)
        if expected_mime and mime_type != expected_mime:
            logger.warning(f"MIME type mismatch for {file.filename}: expected {expected_mime}, got {mime_type}")

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from PDF file with error handling.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            HTTPException: If PDF extraction fails
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path.name}")
            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                if len(reader.pages) == 0:
                    raise HTTPException(status_code=400, detail="PDF file has no pages")
                
                text_parts = []
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text() or ""
                        text_parts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {i+1} of {pdf_path.name}: {e}")
                
                full_text = "\n".join(text_parts)
                
                if not full_text.strip():
                    raise HTTPException(status_code=400, detail="No text could be extracted from PDF")
                
                logger.info(f"Successfully extracted {len(full_text)} characters from {pdf_path.name}")
                return full_text
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path.name}: {e}")
            raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

    def extract_text_from_txt(self, txt_path: Path) -> str:
        """
        Extract text from TXT file with encoding detection.
        
        Args:
            txt_path: Path to the text file
            
        Returns:
            File content as string
            
        Raises:
            HTTPException: If file reading fails
        """
        try:
            logger.info(f"Reading text file: {txt_path.name}")
            
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(txt_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    if not content.strip():
                        raise HTTPException(status_code=400, detail="Text file is empty")
                    
                    logger.info(f"Successfully read {len(content)} characters from {txt_path.name} using {encoding}")
                    return content
                    
                except UnicodeDecodeError:
                    continue
            
            raise HTTPException(status_code=400, detail="Unable to decode text file with any supported encoding")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to read text file {txt_path.name}: {e}")
            raise HTTPException(status_code=500, detail=f"Text file reading failed: {str(e)}")

    def split_text_into_chunks(self, text: str, max_words: int = None) -> List[str]:
        """
        Split text into chunks with improved sentence boundary detection.
        
        Args:
            text: Text to split
            max_words: Maximum words per chunk (defaults to settings value)
            
        Returns:
            List of text chunks
        """
        if max_words is None:
            max_words = settings.CHUNK_SIZE_WORDS
        
        if not text or not text.strip():
            return []
        
        try:
            sentences = sent_tokenize(text)
            chunks = []
            current_chunk = []
            words_in_chunk = 0
            
            for sentence in sentences:
                words = sentence.split()
                sentence_word_count = len(words)
                
                # If single sentence exceeds max_words, split it further
                if sentence_word_count > max_words:
                    # Add current chunk if it has content
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        words_in_chunk = 0
                    
                    # Split long sentence into word-based chunks
                    for i in range(0, sentence_word_count, max_words):
                        word_chunk = words[i:i + max_words]
                        chunks.append(" ".join(word_chunk))
                    continue
                
                # Check if adding this sentence would exceed the limit
                if words_in_chunk + sentence_word_count > max_words and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    words_in_chunk = 0
                
                current_chunk.append(sentence)
                words_in_chunk += sentence_word_count
            
            # Add the last chunk if it has content
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            logger.info(f"Split text into {len(chunks)} chunks with max {max_words} words each")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to split text into chunks: {e}")
            # Fallback: return original text as single chunk
            return [text]

    def save_uploaded_file(self, file: UploadFile) -> tuple[Path, int]:
        """
        Save uploaded file to disk with validation.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (file_path, file_size)
            
        Raises:
            HTTPException: If file validation or saving fails
        """
        try:
            # Validate file
            self._validate_file(file)
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(file.filename)
            save_path = self.docs_folder / safe_filename
            
            # Check if file already exists
            if save_path.exists():
                logger.warning(f"File {safe_filename} already exists, overwriting")
            
            # Save file
            file_size = 0
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                file_size = save_path.stat().st_size
            
            logger.info(f"Successfully saved file: {safe_filename} ({file_size} bytes)")
            return save_path, file_size
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise HTTPException(status_code=500, detail=f"File saving failed: {str(e)}")

    def _generate_safe_filename(self, filename: str) -> str:
        """Generate a safe filename by removing dangerous characters."""
        import re
        
        # Remove path separators and dangerous characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(safe_name) > 255:
            name_part = Path(safe_name).stem[:200]
            ext_part = Path(safe_name).suffix
            safe_name = name_part + ext_part
        
        return safe_name

    def list_documents(self) -> List[str]:
        """
        List all documents in the docs folder.
        
        Returns:
            List of document filenames
        """
        try:
            return [
                f.name for f in self.docs_folder.iterdir() 
                if f.is_file() and f.suffix.lower() in settings.ALLOWED_FILE_EXTENSIONS
            ]
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    def get_document_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific document.
        
        Args:
            filename: Name of the document
            
        Returns:
            Dictionary with document information or None if not found
        """
        try:
            file_path = self.docs_folder / filename
            
            if not file_path.exists() or not file_path.is_file():
                return None
            
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            upload_date = datetime.fromtimestamp(stat.st_mtime)
            file_type = file_path.suffix.lower()
            
            # Get text content to calculate stats
            try:
                if file_type == ".pdf":
                    content = self.extract_text_from_pdf(file_path)
                elif file_type == ".txt":
                    content = self.extract_text_from_txt(file_path)
                else:
                    content = ""
                
                character_count = len(content)
                chunks = self.split_text_into_chunks(content)
                chunks_count = len(chunks)
                
            except Exception as e:
                logger.warning(f"Failed to analyze content for {filename}: {e}")
                character_count = None
                chunks_count = 0
            
            return {
                "filename": filename,
                "file_size": file_size,
                "file_type": file_type,
                "upload_date": upload_date,
                "chunks_count": chunks_count,
                "character_count": character_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get document info for {filename}: {e}")
            return None

    def get_document_content(self, filename: str) -> Optional[str]:
        """
        Get the full text content of a document.
        
        Args:
            filename: Name of the document
            
        Returns:
            Document text content or None if not found/error
        """
        try:
            file_path = self.docs_folder / filename
            
            if not file_path.exists() or not file_path.is_file():
                return None
            
            file_type = file_path.suffix.lower()
            
            if file_type == ".pdf":
                return self.extract_text_from_pdf(file_path)
            elif file_type == ".txt":
                return self.extract_text_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file type for content extraction: {file_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get content for {filename}: {e}")
            return None

    def get_document_chunks(self, filename: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all text chunks for a specific document.
        
        Args:
            filename: Name of the document
            
        Returns:
            List of chunk dictionaries or None if not found/error
        """
        try:
            content = self.get_document_content(filename)
            if content is None:
                return None
            
            chunks = self.split_text_into_chunks(content)
            
            chunk_data = []
            for i, chunk_text in enumerate(chunks):
                chunk_data.append({
                    "chunk_index": i,
                    "text": chunk_text,
                    "word_count": len(chunk_text.split()),
                    "character_count": len(chunk_text)
                })
            
            return chunk_data
            
        except Exception as e:
            logger.error(f"Failed to get chunks for {filename}: {e}")
            return None

    def list_documents_detailed(self) -> List[Dict[str, Any]]:
        """
        List all documents with detailed information.
        
        Returns:
            List of document information dictionaries
        """
        try:
            documents = []
            
            for file_path in self.docs_folder.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in settings.ALLOWED_FILE_EXTENSIONS:
                    doc_info = self.get_document_info(file_path.name)
                    if doc_info:
                        documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents with details: {e}")
            return []

    def delete_document(self, filename: str) -> bool:
        """
        Delete a document from the docs folder.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self.docs_folder / filename
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"Deleted document: {filename}")
                return True
            else:
                logger.warning(f"Document not found for deletion: {filename}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete document {filename}: {e}")
            return False