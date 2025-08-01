# app.py
import streamlit as st
import requests
import os
from typing import Dict, Any, List

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

def get_api_url(endpoint: str) -> str:
    """Get full API URL for an endpoint."""
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
        response = requests.post(get_api_url("/upload"), files=files, timeout=30)
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
        response = requests.get(get_api_url("/list"), timeout=10)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get documents: {str(e)}"}

def ask_question(question: str, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question to the backend."""
    try:
        params = {"q": question, "top_k": top_k}
        response = requests.get(get_api_url("/ask"), params=params, timeout=60)
        
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
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": "Backend unhealthy"}
    except:
        return {"success": False, "error": "Backend unavailable"}

def get_document_info(filename: str) -> Dict[str, Any]:
    """Get detailed information about a document."""
    try:
        response = requests.get(get_api_url(f"/documents/{filename}/info"), timeout=10)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get document info: {str(e)}"}

def get_document_content(filename: str) -> Dict[str, Any]:
    """Get the full text content of a document."""
    try:
        response = requests.get(get_api_url(f"/documents/{filename}/content"), timeout=30)
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get document content: {str(e)}"}

def get_document_preview(filename: str, max_chars: int = 500) -> Dict[str, Any]:
    """Get a preview of document content."""
    try:
        response = requests.get(
            get_api_url(f"/documents/{filename}/preview"), 
            params={"max_chars": max_chars},
            timeout=10
        )
        if response.ok:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": handle_api_error(response)}
    except Exception as e:
        return {"success": False, "error": f"Failed to get document preview: {str(e)}"}

def download_document(filename: str) -> str:
    """Generate download URL for a document."""
    return get_api_url(f"/documents/{filename}/download")

def delete_document(filename: str) -> Dict[str, Any]:
    """Delete a document."""
    try:
        response = requests.delete(get_api_url(f"/documents/{filename}"), timeout=10)
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
    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file", 
        type=["pdf", "txt"],
        help="Upload documents to ask questions about them"
    )
    
    if uploaded_file is not None:
        with st.spinner("Uploading and processing..."):
            upload_result = upload_file(uploaded_file)
        
        if upload_result["success"]:
            upload_data = upload_result["data"]
            st.success(f"✅ Uploaded: {upload_data['filename']}")
            st.info(f"Created {upload_data.get('chunks_created', 0)} text chunks")
            # Refresh page to update document list
            st.rerun()
        else:
            st.error(f"❌ Upload failed: {upload_result['error']}")

    st.markdown("---")
    
    # Documents List Section
    st.subheader("📚 Your Documents")
    
    docs_result = get_documents()
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
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"Preview", key=f"preview_{doc['filename']}"):
                            preview_result = get_document_preview(doc['filename'])
                            if preview_result["success"]:
                                preview_data = preview_result["data"]
                                st.text_area(
                                    "Document Preview:", 
                                    preview_data["preview"], 
                                    height=200,
                                    key=f"preview_text_{doc['filename']}"
                                )
                                if preview_data["is_truncated"]:
                                    st.info(f"Showing first {preview_data['preview_characters']} of {preview_data['total_characters']} characters")
                            else:
                                st.error(preview_result["error"])
                    
                    with col2:
                        download_url = download_document(doc['filename'])
                        st.markdown(f"[� Download]({download_url})")
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{doc['filename']}", type="secondary"):
                            if st.session_state.get(f"confirm_delete_{doc['filename']}", False):
                                delete_result = delete_document(doc['filename'])
                                if delete_result["success"]:
                                    st.success(f"Deleted {doc['filename']}")
                                    st.rerun()
                                else:
                                    st.error(delete_result["error"])
                            else:
                                st.session_state[f"confirm_delete_{doc['filename']}"] = True
                                st.warning("Click delete again to confirm")
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
