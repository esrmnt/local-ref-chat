"""
Unit tests for file upload functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO

from backend.api.knowledge import router as knowledge_router


class TestUploadAPI:
    """Test cases for the upload/knowledge API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(knowledge_router)
        self.client = TestClient(self.app)
    
    def create_test_file(self, filename: str, content: str = "test content") -> BytesIO:
        """Create a test file for upload."""
        file_obj = BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj
    
    @patch('backend.api.knowledge.doc_manager')
    @patch('backend.api.knowledge.indexer')
    def test_upload_success(self, mock_indexer, mock_doc_manager):
        """Test successful file upload."""
        # Mock responses
        mock_doc_manager.save_uploaded_file.return_value = ("/path/test.txt", 1000)
        mock_indexer.add_document.return_value = 5
        
        # Create test file
        test_file = self.create_test_file("test.txt")
        
        response = self.client.post(
            "/upload",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["file_size"] == 1000
        assert data["chunks_created"] == 5
        assert "successfully" in data["message"]
    
    @patch('backend.api.knowledge.doc_manager')
    @patch('backend.api.knowledge.indexer')
    def test_upload_with_indexing_fallback(self, mock_indexer, mock_doc_manager):
        """Test upload with fallback to full rebuild when incremental indexing fails."""
        # Mock responses
        mock_doc_manager.save_uploaded_file.return_value = ("/path/test.txt", 1000)
        mock_indexer.add_document.side_effect = Exception("Incremental indexing failed")
        mock_indexer.rebuild.return_value = (3, 15)  # docs, chunks
        
        test_file = self.create_test_file("test.txt")
        
        response = self.client.post(
            "/upload",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_created"] == 15  # From rebuild
    
    def test_upload_no_file(self):
        """Test upload with no file provided."""
        response = self.client.post("/upload")
        assert response.status_code == 422  # Validation error
    
    def test_upload_empty_filename(self):
        """Test upload with empty filename."""
        response = self.client.post(
            "/upload",
            files={"file": ("", BytesIO(b"content"), "text/plain")}
        )
        assert response.status_code == 400
    
    @patch('backend.api.knowledge.doc_manager')
    def test_upload_doc_manager_error(self, mock_doc_manager):
        """Test upload when document manager raises an error."""
        mock_doc_manager.save_uploaded_file.side_effect = Exception("Save failed")
        
        test_file = self.create_test_file("test.txt")
        
        response = self.client.post(
            "/upload",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
        
        assert response.status_code == 500
    
    @patch('backend.api.knowledge.doc_manager')
    def test_list_documents_success(self, mock_doc_manager):
        """Test successful document listing."""
        mock_doc_manager.list_documents.return_value = ["doc1.pdf", "doc2.txt"]
        
        response = self.client.get("/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert "doc1.pdf" in data["documents"]
        assert "doc2.txt" in data["documents"]
    
    @patch('backend.api.knowledge.doc_manager')
    def test_list_documents_empty(self, mock_doc_manager):
        """Test listing when no documents exist."""
        mock_doc_manager.list_documents.return_value = []
        
        response = self.client.get("/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["documents"] == []
    
    @patch('backend.api.knowledge.doc_manager')
    def test_list_documents_error(self, mock_doc_manager):
        """Test listing when an error occurs."""
        mock_doc_manager.list_documents.side_effect = Exception("List failed")
        
        response = self.client.get("/list")
        
        assert response.status_code == 500
    
    @patch('backend.api.knowledge.indexer')
    @patch('backend.api.knowledge.doc_manager')
    def test_delete_document_success(self, mock_doc_manager, mock_indexer):
        """Test successful document deletion."""
        mock_indexer.remove_document.return_value = 3
        mock_doc_manager.delete_document.return_value = True
        
        response = self.client.delete("/documents/test.txt")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        assert data["chunks_removed"] == 3
    
    @patch('backend.api.knowledge.doc_manager')
    def test_delete_document_not_found(self, mock_doc_manager):
        """Test deleting non-existent document."""
        mock_doc_manager.delete_document.return_value = False
        
        response = self.client.delete("/documents/nonexistent.txt")
        
        assert response.status_code == 404
    
    def test_delete_document_empty_filename(self):
        """Test deleting with empty filename."""
        response = self.client.delete("/documents/")
        assert response.status_code == 404  # Path not found
    
    @patch('backend.api.knowledge.indexer')
    def test_reindex_success(self, mock_indexer):
        """Test successful manual reindexing."""
        mock_indexer.rebuild.return_value = (5, 25)  # docs, chunks
        
        response = self.client.post("/reindex")
        
        assert response.status_code == 200
        data = response.json()
        assert "completed successfully" in data["message"]
        assert data["documents_processed"] == 5
        assert data["chunks_created"] == 25
    
    @patch('backend.api.knowledge.indexer')
    def test_reindex_error(self, mock_indexer):
        """Test reindexing when an error occurs."""
        mock_indexer.rebuild.side_effect = Exception("Rebuild failed")
        
        response = self.client.post("/reindex")
        
        assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__])