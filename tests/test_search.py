"""
Unit tests for search functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.api.search import router as search_router
from backend.models import SearchResponse


class TestSearchAPI:
    """Test cases for the search API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(search_router)
        self.client = TestClient(self.app)
        
        # Mock the indexer
        self.mock_indexer = Mock()
        
    @patch('backend.api.search.indexer')
    def test_keyword_search_success(self, mock_indexer):
        """Test successful keyword search."""
        # Mock response
        mock_results = [
            {
                "filename": "test.txt",
                "chunk_index": 0,
                "text_snippet": "This is a test snippet",
                "citation": "[Source: test.txt, chunk 0]"
            }
        ]
        mock_indexer.keyword_search.return_value = mock_results
        
        response = self.client.get("/search?q=test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["filename"] == "test.txt"
    
    @patch('backend.api.search.indexer')
    def test_keyword_search_empty_query(self, mock_indexer):
        """Test keyword search with empty query."""
        response = self.client.get("/search?q=")
        assert response.status_code == 422  # Validation error
    
    @patch('backend.api.search.indexer')
    def test_keyword_search_case_sensitive(self, mock_indexer):
        """Test keyword search with case sensitivity parameter."""
        mock_indexer.keyword_search.return_value = []
        
        response = self.client.get("/search?q=Test&case_sensitive=true")
        
        assert response.status_code == 200
        mock_indexer.keyword_search.assert_called_once_with("Test", case_sensitive=True)
    
    @patch('backend.api.search.indexer')
    def test_semantic_search_success(self, mock_indexer):
        """Test successful semantic search."""
        mock_results = [
            {
                "filename": "test.txt",
                "chunk_index": 0,
                "text_snippet": "This is a test snippet",
                "citation": "[Source: test.txt, chunk 0]",
                "similarity": 0.85
            }
        ]
        mock_indexer.semantic_search.return_value = mock_results
        
        response = self.client.get("/semantic_search?q=machine learning")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "machine learning"
        assert data["total_results"] == 1
        assert data["results"][0]["similarity"] == 0.85
    
    @patch('backend.api.search.indexer')
    def test_semantic_search_with_top_k(self, mock_indexer):
        """Test semantic search with custom top_k parameter."""
        mock_indexer.semantic_search.return_value = []
        
        response = self.client.get("/semantic_search?q=test&top_k=10")
        
        assert response.status_code == 200
        mock_indexer.semantic_search.assert_called_once_with("test", top_k=10)
    
    @patch('backend.api.search.indexer')
    def test_semantic_search_invalid_top_k(self, mock_indexer):
        """Test semantic search with invalid top_k values."""
        # Too low
        response = self.client.get("/semantic_search?q=test&top_k=0")
        assert response.status_code == 422
        
        # Too high (assuming MAX_TOP_K is 20)
        response = self.client.get("/semantic_search?q=test&top_k=25")
        assert response.status_code == 422
    
    @patch('backend.api.search.indexer')
    def test_search_stats_success(self, mock_indexer):
        """Test getting search statistics."""
        mock_stats = {
            "documents_count": 5,
            "chunks_count": 25,
            "embedding_dimension": 384
        }
        mock_indexer.get_stats.return_value = mock_stats
        
        response = self.client.get("/search/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["documents_count"] == 5
        assert data["chunks_count"] == 25
        assert data["embedding_dimension"] == 384
    
    @patch('backend.api.search.indexer')
    def test_search_error_handling(self, mock_indexer):
        """Test error handling in search endpoints."""
        mock_indexer.keyword_search.side_effect = Exception("Search failed")
        
        response = self.client.get("/search?q=test")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__])