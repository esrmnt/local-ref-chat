# app.py
import streamlit as st
import requests
import os
from typing import Dict, Any, List

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"
API_TIMEOUT = 60  # seconds

def get_api_url(endpoint: str) -> str:
    """Get full API URL forendpoint."""
    return f"{API_URL}{API_PREFIX}{endpoint}"

def handle_api_error(response: requests.Response) -> str:
    """Handle API error responses."""
    try:
        error_data = response.json()
        return error_data.get("detail", f"API Error: {response.status_code}")
    except:
        return f"API Error: {response.status_code} - {response.text}"

def upload_file(uploaded_file) -> Dict[str, Any]:
    """Upload a file to the backend."""
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    
    try:
        response = requests.post(get_api_url("/upload"), files=files, timeout=API_TIMEOUT)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Upload timeout - file may be too large"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend service"}
    except Exception as e:
        return {"success": False, "error": f"Upload failed: {str(e)}"}

def get_documents() -> Dict[str, Any]:
    """Get list of uploaded documents."""
    try:
        response = requests.get(get_api_url("/list"), timeout=API_TIMEOUT)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get documents: {str(e)}"}

def get_documents_cached() -> Dict[str, Any]:
    """Fetch documents with caching to avoid unnecessary API calls."""
    # Check if we need to refresh the cache
    should_refresh = (
        st.session_state.documents_cache is None or 
        st.session_state.get('force_documents_refresh', False)
    )
    
    if should_refresh:
        docs_result = get_documents()
        if docs_result["success"]:
            # Calculate a simple hash of document filenames to detect changes
            documents = docs_result["data"].get("documents", [])
            current_hash = hash(tuple(sorted([doc['filename'] for doc in documents])))
            
            # Update cache
            st.session_state.documents_cache = docs_result
            st.session_state.last_documents_hash = current_hash
            st.session_state.force_documents_refresh = False
        else:
            # Return error but don't cache it
            return docs_result
    
    return st.session_state.documents_cache

def force_documents_refresh():
    """Force refresh of documents cache on next access."""
    st.session_state.force_documents_refresh = True

def clear_upload_state():
    """Clear upload state to allow new uploads."""
    st.session_state.last_uploaded_file = None
    st.session_state.upload_in_progress = False

def ask_question(question: str, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question to the backend."""
    try:
        params = {"q": question, "top_k": top_k}
        response = requests.get(get_api_url("/ask"), params=params, timeout=API_TIMEOUT)
        
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Question processing timeout - please try again"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend service"}
    except Exception as e:
        return {"success": False, "error": f"Question processing failed: {str(e)}"}

def check_backend_status() -> Dict[str, Any]:
    """Check if backend is available."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=API_TIMEOUT)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": "Backend unhealthy"}
    except:
        return {"success": False, "error": "Backend unavailable"}

def get_document_info(filename: str) -> Dict[str, Any]:
    """Get detailed information about a document."""
    try:
        response = requests.get(get_api_url(f"/documents/{filename}/info"), timeout=API_TIMEOUT)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get document info: {str(e)}"}

def get_document_content(filename: str) -> Dict[str, Any]:
    """Get the full text content of a document."""
    try:
        response = requests.get(get_api_url(f"/documents/{filename}/content"), timeout=API_TIMEOUT)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get document content: {str(e)}"}

def download_document(filename: str) -> str:
    """Generate download URL for a document."""
    return get_api_url(f"/documents/{filename}/download")

def delete_document(filename: str) -> Dict[str, Any]:
    """Delete a document."""
    try:
        response = requests.delete(get_api_url(f"/documents/{filename}"), timeout=API_TIMEOUT)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to delete document: {str(e)}"}

# Streamlit App Configuration
st.set_page_config(
    page_title="Reference Chat Assistant", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'backend_status' not in st.session_state:
    st.session_state.backend_status = None

# Document management cache to avoid reloading on every question
if 'documents_cache' not in st.session_state:
    st.session_state.documents_cache = None
    
if 'last_documents_hash' not in st.session_state:
    st.session_state.last_documents_hash = None

# Upload state management to prevent infinite loops
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None
    
if 'upload_in_progress' not in st.session_state:
    st.session_state.upload_in_progress = False

# Header
st.title("📄🔍 Reference Chat Assistant")
st.markdown("*AI-powered chat with your documents - completely local and private*")

# Check backend status
with st.spinner("Checking backend status..."):
    status_result = check_backend_status()
    st.session_state.backend_status = status_result

if not status_result["success"]:
    st.error(f"⚠️ Backend Service Issue: {status_result['error']}")
    st.info("Please ensure the backend server is running on http://localhost:8000")
    st.stop()

# Display backend status
status_data = status_result.get("data", {})
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Status", status_data.get("status", "Unknown"))
with col2:
    st.metric("Documents", status_data.get("documents_count", 0))
with col3:
    st.metric("Chunks", status_data.get("chunks_count", 0))

# Sidebar: Upload & Documents Management
with st.sidebar:
    st.header("📁 Document Management")
    
    # File Upload Section
    st.subheader("Upload Document")
    
    # Show upload status if in progress
    if st.session_state.upload_in_progress:
        st.warning("⏳ Upload in progress... Please wait.")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file", 
        type=["pdf", "txt"],
        help="Upload documents to ask questions about them",
        disabled=st.session_state.upload_in_progress
    )
    
    if uploaded_file is not None:
        # Create a unique identifier for the uploaded file
        file_id = f"{uploaded_file.name}_{uploaded_file.size}_{hash(uploaded_file.getvalue())}"
        
        # Only process if this is a new file (not the same file from previous run)
        if (not st.session_state.upload_in_progress and 
            st.session_state.last_uploaded_file != file_id):
            
            st.session_state.upload_in_progress = True
            st.session_state.last_uploaded_file = file_id
            
            with st.spinner("Uploading and processing..."):
                upload_result = upload_file(uploaded_file)
            
            st.session_state.upload_in_progress = False
            
            if upload_result["success"]:
                upload_data = upload_result["data"]
                st.success(f"✅ Uploaded: {upload_data['filename']}")
                st.info(f"Created {upload_data.get('chunks_created', 0)} text chunks")
                # Force refresh of documents cache and UI
                force_documents_refresh()
                st.rerun()
            else:
                st.error(f"❌ Upload failed: {upload_result['error']}")
                # Reset the file tracking on error so user can retry
                st.session_state.last_uploaded_file = None
    
    # Debug/reset option (only show if there are issues)
    if st.session_state.get('last_uploaded_file') and not st.session_state.upload_in_progress:
        if st.button("🔄 Reset Upload State", help="Click if upload seems stuck"):
            clear_upload_state()
            st.rerun()

    st.markdown("---")
    
    # Documents List Section
    st.subheader("📚 Your Documents")
    
    docs_result = get_documents_cached()

    if docs_result["success"]:
        docs_data = docs_result["data"]
        documents = docs_data.get("documents", [])
        
        if documents:
            st.write(f"**Total: {docs_data.get('total_count', len(documents))} documents**")
            
            # Document management
            for doc in documents:
                with st.expander(f"📄 {doc['filename']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Size:** {doc['file_size']:,} bytes")
                        st.write(f"**Type:** {doc['file_type']}")
                        st.write(f"**Chunks:** {doc['chunks_count']}")
                    
                    with col2:
                        if doc.get('upload_date'):
                            upload_date = doc['upload_date'][:19]  # Remove timezone info for display
                            st.write(f"**Uploaded:** {upload_date}")
                        if doc.get('character_count'):
                            st.write(f"**Characters:** {doc['character_count']:,}")
                    
                    # Action buttons - Download and Delete only (removed preview)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        download_url = download_document(doc['filename'])
                        st.markdown(f"[⬇️ Download]({download_url})")
                    
                    with col2:
                        download_url = download_document(doc['filename'])
                        st.markdown(f"[� Download]({download_url})")
                    
                    with col2:
                        # Improved delete functionality with proper confirmation
                        delete_key = f"delete_{doc['filename']}"
                        confirm_key = f"confirm_delete_state_{doc['filename']}"  # Changed to avoid widget key conflict
                        
                        if st.session_state.get(confirm_key, False):
                            # Confirmation state - show final delete button
                            col2a, col2b = st.columns(2)
                            with col2a:
                                if st.button(f"✅ Confirm", key=f"confirm_btn_{doc['filename']}", type="primary"):
                                    with st.spinner(f"Deleting {doc['filename']}..."):
                                        delete_result = delete_document(doc['filename'])
                                    if delete_result["success"]:
                                        st.success(f"✅ Deleted {doc['filename']}")
                                        # Clear confirmation state and force refresh
                                        del st.session_state[confirm_key]
                                        force_documents_refresh()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Delete failed: {delete_result['error']}")
                                        del st.session_state[confirm_key]
                            
                            with col2b:
                                # Cancel button
                                if st.button(f"❌ Cancel", key=f"cancel_btn_{doc['filename']}", type="secondary"):
                                    del st.session_state[confirm_key]
                                    st.rerun()
                        else:
                            # Initial delete button
                            if st.button(f"🗑️ Delete", key=delete_key, type="secondary"):
                                st.session_state[confirm_key] = True
                                st.rerun()
        else:
            st.info("No documents uploaded yet.")
    else:
        st.error(f"Failed to load documents: {docs_result['error']}")
    
    # Settings
    st.markdown("---")
    st.subheader("⚙️ Search Settings")
    top_k = st.slider(
        "Context chunks", 
        min_value=1, 
        max_value=10, 
        value=5,
        help="Number of relevant document chunks to use for answering"
    )

# Main Chat Interface
st.header("💬 Chat with Your Documents")

# Display chat history
if st.session_state.chat_history:
    for i, chat in enumerate(st.session_state.chat_history):
        if chat["role"] == "user":
            with st.chat_message("user"):
                st.write(chat["content"])
        else:
            with st.chat_message("assistant"):
                st.write(chat["content"])
                
                # Show references if available
                if chat.get("references"):
                    with st.expander(f"📚 Sources ({len(chat['references'])} documents)", expanded=False):
                        for ref in chat["references"]:
                            similarity = ref.get('similarity')
                            similarity_text = f" (similarity: {similarity:.3f})" if similarity else ""
                            
                            st.markdown(f"""
                            **{ref['filename']}**{similarity_text}
                            
                            {ref['text_snippet']}
                            
                            *{ref['citation']}*
                            
                            ---
                            """)

# Chat input
if not st.session_state.chat_history:
    st.info("👋 Welcome! Upload some documents and ask me questions about them.")

user_question = st.chat_input(
    "Ask a question about your documents...",
    disabled=not docs_result.get("success", False) or not docs_result.get("data", {}).get("documents")
)

if user_question and user_question.strip():
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user", 
        "content": user_question
    })
    
    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_question)
    
    # Show thinking message
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.write("🤔 Thinking...")
        
        # Get answer from backend
        answer_result = ask_question(user_question, top_k)
        
        if answer_result["success"]:
            answer_data = answer_result["data"]
            answer = answer_data.get("answer", "No answer received.")
            context = answer_data.get("context", [])
            
            # Replace thinking message with actual answer
            thinking_placeholder.write(answer)
            
            # Show sources
            if context:
                with st.expander(f"📚 Sources ({len(context)} documents)", expanded=False):
                    for ref in context:
                        similarity = ref.get('similarity')
                        similarity_text = f" (similarity: {similarity:.3f})" if similarity else ""
                        
                        st.markdown(f"""
                        **{ref['filename']}**{similarity_text}
                        
                        {ref['text_snippet']}
                        
                        *{ref['citation']}*
                        
                        ---
                        """)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "references": context
            })
            
        else:
            error_msg = f"❌ Error: {answer_result['error']}"
            thinking_placeholder.write(error_msg)
            
            # Add error to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "references": []
            })

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Reference Chat - Your documents, your AI, your privacy 🔒
</div>
""", unsafe_allow_html=True)
