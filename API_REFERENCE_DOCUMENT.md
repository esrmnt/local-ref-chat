# Document Content APIs

This document describes the APIs available for accessing the content of documents stored in the `docs` folder.

## Overview

The `docs` folder stores the uploaded PDF and TXT documents. The following APIs provide various ways to access and interact with these stored documents.

## Document Management APIs

### 1. List Documents (Enhanced)
**GET** `/api/v1/list`

Returns detailed information about all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "filename": "example.pdf",
      "file_size": 1024000,
      "file_type": ".pdf",
      "upload_date": "2025-08-01T10:30:00",
      "chunks_count": 25,
      "character_count": 50000
    }
  ],
  "total_count": 1
}
```

### 2. Get Document Information
**GET** `/api/v1/documents/{filename}/info`

Get detailed metadata about a specific document.

**Example:** `GET /api/v1/documents/example.pdf/info`

**Response:**
```json
{
  "filename": "example.pdf",
  "file_size": 1024000,
  "file_type": ".pdf",
  "upload_date": "2025-08-01T10:30:00",
  "chunks_count": 25,
  "character_count": 50000
}
```

### 3. Get Document Content
**GET** `/api/v1/documents/{filename}/content`

Retrieve the full extracted text content of a document.

**Example:** `GET /api/v1/documents/example.pdf/content`

**Response:**
```json
{
  "filename": "example.pdf",
  "content": "Full text content of the document...",
  "file_type": ".pdf",
  "character_count": 50000,
  "word_count": 8500
}
```

### 4. Get Document Preview
**GET** `/api/v1/documents/{filename}/preview?max_chars=1000`

Get a preview of the document content (first N characters).

**Parameters:**
- `max_chars`: Maximum characters to return (1-10000, default: 1000)

**Example:** `GET /api/v1/documents/example.pdf/preview?max_chars=500`

**Response:**
```json
{
  "filename": "example.pdf",
  "preview": "Beginning of document content...",
  "is_truncated": true,
  "total_characters": 50000,
  "preview_characters": 500
}
```

### 5. Get Document Chunks
**GET** `/api/v1/documents/{filename}/chunks`

Get all text chunks created from a document during processing.

**Example:** `GET /api/v1/documents/example.pdf/chunks`

**Response:**
```json
{
  "filename": "example.pdf",
  "total_chunks": 25,
  "chunks": [
    {
      "chunk_index": 0,
      "text": "First chunk of text...",
      "word_count": 120,
      "character_count": 800
    },
    {
      "chunk_index": 1,
      "text": "Second chunk of text...",
      "word_count": 115,
      "character_count": 750
    }
  ]
}
```

### 6. Get Indexed Chunks
**GET** `/api/v1/documents/{filename}/indexed-chunks`

Get the chunks as they exist in the search index (with processing metadata).

**Example:** `GET /api/v1/documents/example.pdf/indexed-chunks`

**Response:**
```json
{
  "filename": "example.pdf",
  "total_indexed_chunks": 25,
  "chunks": [
    {
      "chunk_id": 0,
      "chunk_index": 0,
      "text": "First chunk of text...",
      "filename": "example.pdf",
      "doc_id": 0,
      "word_count": 120,
      "character_count": 800,
      "has_embedding": true
    }
  ]
}
```

### 7. Download Document
**GET** `/api/v1/documents/{filename}/download`

Download the original document file.

**Example:** `GET /api/v1/documents/example.pdf/download`

**Response:** File download with appropriate MIME type

### 8. Delete Document
**DELETE** `/api/v1/documents/{filename}`

Delete a document and remove it from the index.

**Example:** `DELETE /api/v1/documents/example.pdf`

**Response:**
```json
{
  "message": "Document 'example.pdf' deleted successfully",
  "chunks_removed": 25
}
```

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get list of all documents
response = requests.get(f"{BASE_URL}/list")
documents = response.json()["documents"]

# Get content of a specific document
doc_filename = documents[0]["filename"]
response = requests.get(f"{BASE_URL}/documents/{doc_filename}/content")
content = response.json()["content"]

# Get preview of a document
response = requests.get(f"{BASE_URL}/documents/{doc_filename}/preview", 
                       params={"max_chars": 500})
preview = response.json()["preview"]

# Download a document
response = requests.get(f"{BASE_URL}/documents/{doc_filename}/download")
with open(f"downloaded_{doc_filename}", "wb") as f:
    f.write(response.content)

# Get document chunks
response = requests.get(f"{BASE_URL}/documents/{doc_filename}/chunks")
chunks = response.json()["chunks"]
```

### cURL Examples

```bash
# List documents
curl "http://localhost:8000/api/v1/list"

# Get document info
curl "http://localhost:8000/api/v1/documents/example.pdf/info"

# Get document content
curl "http://localhost:8000/api/v1/documents/example.pdf/content"

# Get document preview
curl "http://localhost:8000/api/v1/documents/example.pdf/preview?max_chars=500"

# Download document
curl -O "http://localhost:8000/api/v1/documents/example.pdf/download"

# Delete document
curl -X DELETE "http://localhost:8000/api/v1/documents/example.pdf"
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **404**: Document not found
- **500**: Server error

Error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Frontend Integration

The Streamlit frontend now includes:

- **Document Browser**: View all documents with metadata
- **Content Preview**: Quick preview of document content
- **Download Links**: Direct download of original files
- **Document Management**: Delete documents with confirmation
- **Document Statistics**: File size, chunk count, character count

## Security Notes

- File access is restricted to the configured `docs` folder
- Filename validation prevents directory traversal attacks
- File size limits are enforced during upload
- Only supported file types (.pdf, .txt) are accessible
- All file operations include proper error handling

## Performance Considerations

- Content extraction is cached where possible
- Large documents may take time to process
- Preview endpoints are optimized for quick responses
- Chunk data is retrieved from the in-memory index when available
