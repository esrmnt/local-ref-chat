import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor
import threading

from backend.settings import settings
from backend.core.utils import clean_text, format_snippet, render_citation
from backend.logging_config import get_logger

logger = get_logger(__name__)

class Indexer:
    """Handles document indexing and search operations."""
    
    def __init__(self, embedding_model_name: str = None):
        self.index: Dict[int, Dict[str, Any]] = {}
        self.documents: Dict[int, str] = {}
        self.preview_text_length = 250
        self._lock = threading.RLock()  # For thread safety
        
        # Initialize embedding model
        model_name = embedding_model_name or settings.EMBEDDING_MODEL_NAME
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise

    def rebuild(self, doc_manager) -> tuple[int, int]:
        """
        Rebuild the entire index from documents in the document manager.
        
        Args:
            doc_manager: DocumentManager instance
            
        Returns:
            Tuple of (documents_processed, chunks_created)
        """
        with self._lock:
            logger.info("Starting index rebuild...")
            
            doc_id = 0
            chunk_id = 0
            documents_processed = 0
            chunks_created = 0
            
            # Clear existing index
            self.documents.clear()
            self.index.clear()

            if not doc_manager.docs_folder.exists():
                logger.warning("Docs folder not found, skipping indexing.")
                return 0, 0

            # Process each file
            for file_path in doc_manager.docs_folder.iterdir():
                if not file_path.is_file():
                    continue
                    
                file_ext = file_path.suffix.lower()
                if file_ext not in settings.ALLOWED_FILE_EXTENSIONS:
                    continue

                try:
                    # Extract text based on file type
                    if file_ext == ".pdf":
                        text = doc_manager.extract_text_from_pdf(file_path)
                    elif file_ext == ".txt":
                        text = doc_manager.extract_text_from_txt(file_path)
                    else:
                        logger.warning(f"Unsupported file type: {file_ext}")
                        continue

                    # Clean and store document text
                    clean_text_content = clean_text(text)
                    if not clean_text_content.strip():
                        logger.warning(f"No text content found in {file_path.name}")
                        continue
                        
                    self.documents[doc_id] = clean_text_content

                    # Split into chunks and create embeddings
                    chunks = doc_manager.split_text_into_chunks(clean_text_content)
                    
                    if not chunks:
                        logger.warning(f"No chunks created for {file_path.name}")
                        continue

                    # Process chunks in batches for better performance
                    chunk_embeddings = self._create_embeddings_batch([chunk for chunk in chunks])
                    
                    for i, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                        self.index[chunk_id] = {
                            "text": chunk_text,
                            "doc_id": doc_id,
                            "filename": file_path.name,
                            "chunk_index": i,
                            "embedding": embedding
                        }
                        chunk_id += 1
                        chunks_created += 1

                    documents_processed += 1
                    logger.info(f"Indexed {file_path.name}: {len(chunks)} chunks")
                    
                except Exception as e:
                    logger.error(f"Failed to index {file_path.name}: {e}")
                    continue
                    
                doc_id += 1

            logger.info(f"Index rebuild completed: {documents_processed} documents, {chunks_created} chunks")
            return documents_processed, chunks_created

    def _create_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Create embeddings for a batch of texts for better performance."""
        try:
            if not texts:
                return []
                
            # Create embeddings in batch
            embeddings = self.embedding_model.encode(
                texts, 
                batch_size=32,  # Process in smaller batches to manage memory
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            return [emb for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to create embeddings batch: {e}")
            # Fallback: create embeddings one by one
            return [self.embedding_model.encode(text) for text in texts]

    def add_document(self, doc_manager, file_path) -> int:
        """
        Add a single document to the index without rebuilding everything.
        
        Args:
            doc_manager: DocumentManager instance
            file_path: Path to the document to add
            
        Returns:
            Number of chunks created for this document
        """
        with self._lock:
            try:
                logger.info(f"Adding document to index: {file_path.name}")
                
                # Get next doc_id
                next_doc_id = max(self.documents.keys()) + 1 if self.documents else 0
                next_chunk_id = max(self.index.keys()) + 1 if self.index else 0
                
                # Extract text
                file_ext = file_path.suffix.lower()
                if file_ext == ".pdf":
                    text = doc_manager.extract_text_from_pdf(file_path)
                elif file_ext == ".txt":
                    text = doc_manager.extract_text_from_txt(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")

                # Clean and store
                clean_text_content = clean_text(text)
                self.documents[next_doc_id] = clean_text_content

                # Create chunks and embeddings
                chunks = doc_manager.split_text_into_chunks(clean_text_content)
                chunk_embeddings = self._create_embeddings_batch(chunks)
                
                chunks_created = 0
                for i, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                    self.index[next_chunk_id + i] = {
                        "text": chunk_text,
                        "doc_id": next_doc_id,
                        "filename": file_path.name,
                        "chunk_index": i,
                        "embedding": embedding
                    }
                    chunks_created += 1

                logger.info(f"Successfully added {file_path.name}: {chunks_created} chunks")
                return chunks_created
                
            except Exception as e:
                logger.error(f"Failed to add document {file_path.name}: {e}")
                raise

    def remove_document(self, filename: str) -> int:
        """
        Remove all chunks for a specific document from the index.
        
        Args:
            filename: Name of the document to remove
            
        Returns:
            Number of chunks removed
        """
        with self._lock:
            try:
                logger.info(f"Removing document from index: {filename}")
                
                chunks_to_remove = []
                doc_ids_to_remove = set()
                
                # Find chunks and docs to remove
                for chunk_id, chunk_data in self.index.items():
                    if chunk_data["filename"] == filename:
                        chunks_to_remove.append(chunk_id)
                        doc_ids_to_remove.add(chunk_data["doc_id"])
                
                # Remove chunks
                for chunk_id in chunks_to_remove:
                    del self.index[chunk_id]
                
                # Remove documents
                for doc_id in doc_ids_to_remove:
                    if doc_id in self.documents:
                        del self.documents[doc_id]
                
                removed_count = len(chunks_to_remove)
                logger.info(f"Removed {removed_count} chunks for document: {filename}")
                return removed_count
                
            except Exception as e:
                logger.error(f"Failed to remove document {filename}: {e}")
                return 0

    def keyword_search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Perform keyword search across indexed documents.
        
        Args:
            query: Search query
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            List of search results
        """
        try:
            if not query or not query.strip():
                return []
            
            search_query = query if case_sensitive else query.lower()
            results = []
            
            with self._lock:
                for chunk in self.index.values():
                    chunk_text = chunk["text"] if case_sensitive else chunk["text"].lower()
                    
                    if search_query in chunk_text:
                        results.append({
                            "filename": chunk["filename"],
                            "chunk_index": chunk["chunk_index"],
                            "text_snippet": format_snippet(chunk["text"], self.preview_text_length),
                            "citation": render_citation(chunk["filename"], chunk["chunk_index"])
                        })
            
            logger.info(f"Keyword search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed for query '{query}': {e}")
            return []

    def semantic_search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of search results with similarity scores
        """
        try:
            if not query or not query.strip():
                return []
            
            if top_k is None:
                top_k = settings.DEFAULT_TOP_K
            
            # Limit top_k to reasonable bounds
            top_k = min(max(1, top_k), settings.MAX_TOP_K)
            
            logger.info(f"Performing semantic search for query: '{query}' (top_k={top_k})")
            
            # Create query embedding
            query_emb = self.embedding_model.encode(query)
            
            similarities = []
            
            with self._lock:
                if not self.index:
                    logger.warning("No indexed documents for semantic search")
                    return []
                
                # Calculate similarities
                for chunk_id, chunk in self.index.items():
                    try:
                        chunk_emb = chunk["embedding"]
                        similarity = self._cosine_similarity(query_emb, chunk_emb)
                        similarities.append((similarity, chunk))
                    except Exception as e:
                        logger.warning(f"Failed to calculate similarity for chunk {chunk_id}: {e}")
                        continue
            
            # Sort by similarity and take top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_results = similarities[:top_k]
            
            # Format results
            results = []
            for similarity, chunk in top_results:
                results.append({
                    "filename": chunk["filename"],
                    "chunk_index": chunk["chunk_index"],
                    "similarity": float(similarity),
                    "text_snippet": format_snippet(chunk["text"], self.preview_text_length),
                    "citation": render_citation(chunk["filename"], chunk["chunk_index"])
                })
            
            logger.info(f"Semantic search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed for query '{query}': {e}")
            return []

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Ensure vectors are numpy arrays
            a = np.array(a)
            b = np.array(b)
            
            # Calculate norms
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            # Avoid division by zero
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(a, b) / (norm_a * norm_b)
            
            # Ensure result is in valid range [-1, 1]
            similarity = np.clip(similarity, -1.0, 1.0)
            
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Cosine similarity calculation failed: {e}")
            return 0.0

    def get_document_chunks_indexed(self, filename: str) -> List[Dict[str, Any]]:
        """
        Get all indexed chunks for a specific document.
        
        Args:
            filename: Name of the document
            
        Returns:
            List of indexed chunks with embeddings and metadata
        """
        try:
            chunks = []
            
            with self._lock:
                for chunk_id, chunk_data in self.index.items():
                    if chunk_data["filename"] == filename:
                        chunks.append({
                            "chunk_id": chunk_id,
                            "chunk_index": chunk_data["chunk_index"],
                            "text": chunk_data["text"],
                            "filename": chunk_data["filename"],
                            "doc_id": chunk_data["doc_id"],
                            "word_count": len(chunk_data["text"].split()),
                            "character_count": len(chunk_data["text"]),
                            "has_embedding": chunk_data.get("embedding") is not None
                        })
                
                # Sort by chunk_index
                chunks.sort(key=lambda x: x["chunk_index"])
            
            logger.info(f"Retrieved {len(chunks)} indexed chunks for document: {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get indexed chunks for {filename}: {e}")
            return []

    def get_stats(self) -> Dict[str, int]:
        """Get indexing statistics."""
        with self._lock:
            return {
                "documents_count": len(self.documents),
                "chunks_count": len(self.index),
                "embedding_dimension": len(next(iter(self.index.values()))["embedding"]) if self.index else 0
            }
