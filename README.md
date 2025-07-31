# local-ref-chat

**local-ref-chat** is a local search and RAG (Retrieval-Augmented Generation) chat assistant for your own documents. It runs entirely on your machine, enabling you to upload files, ask natural-language questions, and get contextual, cited answers from a local language model (Ollama). All indexing and search is in-memory (as of today), with modular Python FastAPI architecture.

## 🚩 Features

- **Document upload** (PDF, TXT) from a simple web interface.
- **Document parsing, splitting (chunking), and semantic embedding** on upload.
- **Keyword and semantic search** over all your documents—no cloud, all local.
- **Retrieval-Augmented Q&A**: Ask natural questions and get AI-generated answers grounded in your content, with snippet references.
- **FastAPI backend** using modular, testable code structure.
- **Local LLM (Ollama) integration** for safe, private language model inference.
- **Simple, modern chat UI (work in progress)**: Upload new docs and chat, all in one page.
- **Full in-memory index** for lightweight operation and maximum privacy. This is to be extended with persistent storage in future versions.

## 🏗️ Project Structure


src/
  main.py              # FastAPI app setup
  config.py            # App-wide configuration (chunk size, models, etc.)
  core/
    __init__.py        # Exposes main classes and helpers (public API)
    document_manager.py  # Handles file saving, text extraction, chunking
    indexer.py           # Builds/searches embedding and keyword indexes
    model.py             # Interface to Ollama LLM
    utils.py             # Text cleaning, snippet/citation formatting helpers
    state.py             # Singleton/shared instance management
  api/
    __init__.py         # Exposes API routers
    upload.py           # File upload endpoints
    search.py           # Search endpoints (keyword, semantic)
    chat.py             # /ask endpoint and chat UI endpoint
docs/                  # Your uploaded documents (auto-created)
requirements.txt


## 🚀 Getting Started

### 1. Clone and Setup

```bash
git clone  local-ref-chat
cd local-ref-chat
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run Ollama

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