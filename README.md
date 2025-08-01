# Reference Chat

**Reference Chat** is a production-ready local search and RAG (Retrieval-Augmented Generation) chat assistant for your documents. It runs entirely on your machine, enabling you to upload files, ask natural-language questions, and get contextual, cited answers from a local language model (Ollama). All indexing and search is in-memory with optional persistence, featuring a robust Python FastAPI architecture.

## ✨ Features

- **🔒 Complete Privacy**: Everything runs locally - no data leaves your machine
- **📁 Document Support**: Upload PDF and TXT files with automatic text extraction
- **🧠 Smart Processing**: Automatic document parsing, chunking, and semantic embedding
- **🔍 Dual Search**: Both keyword and semantic search across all documents
- **💬 RAG Chat**: Ask natural questions and get AI-generated answers with source citations
- **📄 Document Access**: Full API access to document content, chunks, and metadata
- **⬇️ File Management**: Download, preview, and manage uploaded documents
- **⚡ High Performance**: Optimized indexing with batch processing and thread safety
- **🛡️ Production Ready**: Comprehensive error handling, logging, and monitoring
- **🎨 Modern UI**: Clean Streamlit interface with real-time chat and document management
- **📊 Analytics**: Built-in search statistics and health monitoring

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── main.py              # Application setup with lifespan management
├── settings.py          # Environment-based configuration
├── models.py            # Pydantic request/response models
├── logging_config.py    # Structured logging setup
├── config.py            # Backward compatibility layer
├── core/
│   ├── document_manager.py # File handling, validation, text extraction
│   ├── indexer.py          # Semantic indexing and search
│   ├── model.py           # Ollama LLM integration
│   ├── utils.py           # Text processing utilities
│   └── state.py           # Application state management
└── api/
    ├── knowledge.py       # Document upload/management endpoints
    ├── search.py          # Search endpoints (keyword/semantic)
    └── chat.py            # RAG chat endpoints
```

### Frontend (Streamlit)
```
frontend/
├── app.py               # Main Streamlit application
├── components/          # Reusable UI components (future)
└── pages/               # Multi-page app structure (future)
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with pip
2. **Ollama** running locally ([Download Ollama](https://ollama.ai/))
3. **Git** for cloning the repository

### Installation

1. **Clone and Setup Environment**
```bash
git clone https://github.com/esrmnt/local-ref-chat.git
cd local-ref-chat

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure Environment (Optional)**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your preferences (all settings have sensible defaults)
```

3. **Start Ollama Service**
```bash
# Pull a model (if not already done)
ollama pull llama3

# Ollama should be running on localhost:11434
ollama serve
```

4. **Run the Application**

Start the backend:
```bash
# From project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend (in a new terminal):
```bash
# From project root
streamlit run frontend/app.py
```

5. **Access the Application**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📖 Usage Guide

### Document Management

1. **Upload Documents**: Use the sidebar to upload PDF or TXT files
2. **View Documents**: See all uploaded documents with metadata in the sidebar
3. **Document Actions**: Preview content, download files, or delete documents
4. **Access Content**: Use the API to programmatically access document content

> 📋 **Document Content APIs**: The system provides comprehensive APIs to access stored document content. See [DOCUMENT_APIS.md](DOCUMENT_APIS.md) for detailed documentation on all available endpoints for content access, preview, chunking, and download.

### Search & Chat

1. **Ask Questions**: Type natural language questions in the chat interface
2. **View Sources**: Expand the "Sources" section to see document citations
3. **Adjust Context**: Use the sidebar slider to control how many document chunks to use

### API Usage

The REST API provides programmatic access:

```python
import requests

# Upload a document
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/upload",
        files={"file": f}
    )

# Search documents
response = requests.get(
    "http://localhost:8000/api/v1/semantic_search",
    params={"q": "machine learning", "top_k": 5}
)

# Ask a question
response = requests.get(
    "http://localhost:8000/api/v1/ask",
    params={"q": "What is machine learning?", "top_k": 5}
)
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```env
# File handling
MAX_FILE_SIZE_MB=50
DOCS_FOLDER=docs

# Text processing
CHUNK_SIZE_WORDS=500

# AI/ML settings
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Ollama settings
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=30

# Search settings
DEFAULT_TOP_K=5
MAX_TOP_K=20

# API settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
```

### Supported Models

- **Embedding Models**: Any sentence-transformers model
- **Ollama Models**: llama3, mistral, codellama, etc.

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

## 📊 Monitoring & Health

### Health Checks

- **Backend Health**: `GET /health`
- **Ollama Status**: `GET /api/v1/ollama/status`
- **Search Stats**: `GET /api/v1/search/stats`

### Logging

Logs are written to:
- Console (stdout)
- `logs/app.log` file

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🔧 Development

### Code Quality

The project follows these best practices:

- **Type Hints**: Full type annotation coverage
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging throughout
- **Testing**: Unit tests for core functionality
- **Documentation**: API docs via FastAPI/OpenAPI
- **Security**: Input validation and file sanitization

### Project Structure

- **Modular Design**: Clear separation of concerns
- **Dependency Injection**: Testable components
- **Configuration Management**: Environment-based settings
- **Thread Safety**: Safe concurrent operations
- **Performance**: Optimized indexing and search

## 🚦 API Endpoints

### Knowledge Management
- `POST /api/v1/upload` - Upload document
- `GET /api/v1/list` - List documents with metadata
- `GET /api/v1/documents/{filename}/info` - Get document information
- `GET /api/v1/documents/{filename}/content` - Get full document content
- `GET /api/v1/documents/{filename}/preview` - Get document preview
- `GET /api/v1/documents/{filename}/chunks` - Get document text chunks
- `GET /api/v1/documents/{filename}/indexed-chunks` - Get indexed chunks with embeddings
- `GET /api/v1/documents/{filename}/download` - Download original document
- `DELETE /api/v1/documents/{filename}` - Delete document
- `POST /api/v1/reindex` - Rebuild search index

### Search
- `GET /api/v1/search` - Keyword search
- `GET /api/v1/semantic_search` - Semantic search
- `GET /api/v1/search/stats` - Search statistics

### Chat
- `GET /api/v1/ask` - Ask a question (RAG)
- `POST /api/v1/ask` - Ask a question (POST method)
- `GET /api/v1/ollama/status` - Check Ollama status

### System
- `GET /health` - Application health check

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.8+ required)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check port 8000 is available

**Ollama not working:**
- Ensure Ollama is installed and running: `ollama serve`
- Check model is available: `ollama list`
- Verify API URL in configuration

**File upload fails:**
- Check file size limits (default 50MB)
- Verify file type is supported (PDF, TXT)
- Check available disk space

**Empty search results:**
- Ensure documents are uploaded and indexed
- Check if questions match document content
- Try different phrasings or keywords

### Performance Tuning

For large document collections:
- Increase `CHUNK_SIZE_WORDS` for longer context
- Use a more powerful embedding model
- Consider implementing vector database storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Sentence Transformers](https://www.sbert.net/) for semantic embeddings
- [Ollama](https://ollama.ai/) for local LLM inference
- [Streamlit](https://streamlit.io/) for the beautiful frontend framework

Make sure [Ollama](https://ollama.com/) is installed and running with your chosen model:

```bash
ollama run llama3      # Or another local model, per your config.py
```

### 3. Start the FastAPI App

```bash
uvicorn src.main:app --reload
```

App runs at: [http://localhost:8000](http://localhost:8000)

## 🖥️ Usage

- **Upload Files:**  
  Visit [http://localhost:8000/upload](http://localhost:8000/upload) to access the main UI.  
  Use the upload box to add PDFs or TXT files.

- **Keyword/Semantic Search:**  
  Use `/search/keyword?q=...` and `/search/semantic?q=...` endpoints (or implement a simple Frontend).

- **Chat with your documents:**  
  Ask questions in the chat window.  
  The system retrieves relevant snippets and generates an AI answer with sources from your docs.

## ✨ Example

**Upload:**  
Choose a PDF/TXT, click Upload.

**Ask a question:**  
```
What are the main points discussed in the 2022 strategy.pdf?
```

**You’ll get (for example):**
```
{
  "answer": "The 2022 strategy.pdf discusses these main points: ...",
  "context": [
    {"filename": "strategy.pdf", "chunk_index": 3, "text_snippet": "...", "citation": "[Source: strategy.pdf, chunk 3]"},
    ...
  ]
}
```

## ⚙️ Configuration

App settings are in `src/config.py`:

- `CHUNK_SIZE_WORDS` — Sentence chunk size for indexing.
- `EMBEDDING_MODEL_NAME` — SentenceTransformers model used for semantic search.
- `OLLAMA_API_URL` and `OLLAMA_MODEL` — base URL and model name for Ollama LLM.
- `DEFAULT_TOP_K` — Number of chunks to retrieve as context for each query.

Adjust these to change performance or accuracy.

## 🧩 Code Quality and Structure

- **Type hints and docstrings** for maintainability. This needs to be improved upon.
- **No circular imports**: Utilities are used only from their modules in core; only public classes/functions exposed via package `__init__.py`.
- **Singleton state**: All routes share the same data/index.
- **Clean separation** of model calls (`core/model.py`), utilities (`core/utils.py`), and business logic.

## 🛠️ Recommended Next Steps

- Add clean UI for search and chat (currently basic).
- Add support for more file types (DOCX, Markdown).
- Persist the document index/embeddings to disk for faster restarts.
- Enhance chat memory for multi-turn dialog.
- Collect feedback with citations, provide an export or summary feature.

## 🤝 Credits

- [FastAPI](https://fastapi.tiangolo.com/) for the API.
- [SentenceTransformers](https://www.sbert.net/) for semantic embeddings.
- [Ollama](https://ollama.com/) for local LLM serving.
- NLTK for sentence segmentation.
- PyPDF2 for robust PDF extraction.

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.