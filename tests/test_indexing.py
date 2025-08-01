"""
Unit tests for the indexing functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from backend.core.document_manager import DocumentManager
from backend.core.indexer import Indexer


class TestDocumentManager:
    """Test cases for DocumentManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.doc_manager = DocumentManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_init_creates_docs_folder(self):
        """Test that DocumentManager creates the docs folder."""
        assert self.doc_manager.docs_folder.exists()
        assert self.doc_manager.docs_folder.is_dir()
    
    def test_split_text_into_chunks(self):
        """Test text chunking functionality."""
        text = "This is a test sentence. " * 50  # 300 words
        chunks = self.doc_manager.split_text_into_chunks(text, max_words=100)
        
        assert len(chunks) > 1
        assert all(len(chunk.split()) <= 100 for chunk in chunks[:-1])
        assert chunks[-1]  # Last chunk should not be empty
    
    def test_split_empty_text(self):
        """Test chunking empty text."""
        chunks = self.doc_manager.split_text_into_chunks("")
        assert chunks == []
    
    def test_split_single_long_sentence(self):
        """Test chunking a single very long sentence."""
        long_sentence = "word " * 200  # 200 words in one sentence
        chunks = self.doc_manager.split_text_into_chunks(long_sentence, max_words=50)
        
        assert len(chunks) == 4  # 200/50 = 4 chunks
        assert all(len(chunk.split()) == 50 for chunk in chunks[:-1])
    
    def test_list_documents_empty(self):
        """Test listing documents when folder is empty."""
        docs = self.doc_manager.list_documents()
        assert docs == []
    
    def test_list_documents_with_files(self):
        """Test listing documents with actual files."""
        # Create test files
        (self.doc_manager.docs_folder / "test1.pdf").touch()
        (self.doc_manager.docs_folder / "test2.txt").touch()
        (self.doc_manager.docs_folder / "ignored.xyz").touch()  # Should be ignored
        
        docs = self.doc_manager.list_documents()
        assert len(docs) == 2
        assert "test1.pdf" in docs
        assert "test2.txt" in docs
        assert "ignored.xyz" not in docs
    
    def test_delete_document_existing(self):
        """Test deleting an existing document."""
        test_file = self.doc_manager.docs_folder / "test.txt"
        test_file.write_text("test content")
        
        result = self.doc_manager.delete_document("test.txt")
        assert result is True
        assert not test_file.exists()
    
    def test_delete_document_nonexistent(self):
        """Test deleting a non-existent document."""
        result = self.doc_manager.delete_document("nonexistent.txt")
        assert result is False
    
    def test_generate_safe_filename(self):
        """Test filename sanitization."""
        unsafe_name = "test<>file|with:bad*chars.txt"
        safe_name = self.doc_manager._generate_safe_filename(unsafe_name)
        
        assert "<" not in safe_name
        assert ">" not in safe_name
        assert "|" not in safe_name
        assert ":" not in safe_name
        assert "*" not in safe_name
        assert safe_name.endswith(".txt")


class TestIndexer:
    """Test cases for Indexer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the embedding model to avoid loading real model in tests
        with patch('backend.core.indexer.SentenceTransformer') as mock_transformer:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1] * 384  # Mock embedding
            mock_transformer.return_value = mock_model
            
            self.indexer = Indexer()
            self.mock_model = mock_model
    
    def test_indexer_initialization(self):
        """Test that Indexer initializes properly."""
        assert hasattr(self.indexer, 'index')
        assert hasattr(self.indexer, 'documents')
        assert hasattr(self.indexer, 'embedding_model')
        assert self.indexer.index == {}
        assert self.indexer.documents == {}
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec_a = [1, 0, 0]
        vec_b = [0, 1, 0]
        vec_c = [1, 0, 0]
        
        # Orthogonal vectors should have similarity 0
        sim_ab = self.indexer._cosine_similarity(vec_a, vec_b)
        assert abs(sim_ab - 0.0) < 1e-10
        
        # Identical vectors should have similarity 1
        sim_ac = self.indexer._cosine_similarity(vec_a, vec_c)
        assert abs(sim_ac - 1.0) < 1e-10
    
    def test_cosine_similarity_zero_vectors(self):
        """Test cosine similarity with zero vectors."""
        vec_zero = [0, 0, 0]
        vec_normal = [1, 2, 3]
        
        sim = self.indexer._cosine_similarity(vec_zero, vec_normal)
        assert sim == 0.0
    
    def test_keyword_search_empty_index(self):
        """Test keyword search on empty index."""
        results = self.indexer.keyword_search("test query")
        assert results == []
    
    def test_keyword_search_with_results(self):
        """Test keyword search with matching content."""
        # Add test content to index
        self.indexer.index[0] = {
            "text": "This is a test document about machine learning.",
            "filename": "test.txt",
            "chunk_index": 0,
            "embedding": [0.1] * 384
        }
        
        results = self.indexer.keyword_search("machine learning")
        assert len(results) == 1
        assert results[0]["filename"] == "test.txt"
        assert "machine learning" in results[0]["text_snippet"].lower()
    
    def test_keyword_search_case_sensitivity(self):
        """Test keyword search case sensitivity."""
        self.indexer.index[0] = {
            "text": "This contains UPPERCASE words.",
            "filename": "test.txt",
            "chunk_index": 0,
            "embedding": [0.1] * 384
        }
        
        # Case insensitive (default)
        results = self.indexer.keyword_search("uppercase")
        assert len(results) == 1
        
        # Case sensitive
        results = self.indexer.keyword_search("uppercase", case_sensitive=True)
        assert len(results) == 0
        
        results = self.indexer.keyword_search("UPPERCASE", case_sensitive=True)
        assert len(results) == 1
    
    def test_semantic_search_empty_index(self):
        """Test semantic search on empty index."""
        results = self.indexer.semantic_search("test query")
        assert results == []
    
    def test_get_stats_empty(self):
        """Test getting stats from empty indexer."""
        stats = self.indexer.get_stats()
        assert stats["documents_count"] == 0
        assert stats["chunks_count"] == 0
        assert stats["embedding_dimension"] == 0
    
    def test_get_stats_with_content(self):
        """Test getting stats with indexed content."""
        self.indexer.documents[0] = "test document"
        self.indexer.index[0] = {
            "text": "test chunk",
            "filename": "test.txt",
            "chunk_index": 0,
            "embedding": [0.1] * 384
        }
        
        stats = self.indexer.get_stats()
        assert stats["documents_count"] == 1
        assert stats["chunks_count"] == 1
        assert stats["embedding_dimension"] == 384


if __name__ == "__main__":
    pytest.main([__file__])