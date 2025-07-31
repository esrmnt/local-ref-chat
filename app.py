# app.py
import streamlit as st
import requests

# Adjust this to your FastAPI server URL if different
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Local Ref Chat Assistant", layout="wide")

# Title
st.title("📄🔍 Local Ref Chat Assistant")

# --- Sidebar: Upload & Documents List ---
with st.sidebar:
    st.header("Upload Document")

    uploaded_file = st.file_uploader("Upload PDF or TXT file", type=["pdf", "txt"])
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        with st.spinner("Uploading..."):
            res = requests.post(f"{API_URL}/upload_ajax", files=files)
        if res.ok:
            st.success(f"Uploaded: {uploaded_file.name}")
        else:
            st.error(f"Upload failed: {res.text}")

    st.markdown("---")
    st.header("Uploaded Documents")

    # Optional: call backend to list docs if you have an endpoint
    try:
        res_docs = requests.get(f"{API_URL}/list_docs")
        if res_docs.ok:
            docs = res_docs.json().get("documents", [])
            if docs:
                for d in docs:
                    st.write(f"- {d}")
            else:
                st.write("No documents uploaded yet.")
        else:
            st.write("Could not load document list.")
    except Exception:
        st.write("Document list unavailable.")

# --- Chat Section ---
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for i, chat in enumerate(st.session_state.chat_history):
    if chat["role"] == "user":
        st.chat_message("user").write(chat["content"])
    else:
        # AI message with references (if any)
        with st.chat_message("assistant"):
            st.write(chat["content"])
            if chat.get("references"):
                with st.expander("References"):
                    for ref in chat["references"]:
                        # Show filename and snippet nicely formatted with citation
                        st.markdown(f"**{ref['filename']}**: {ref['text_snippet']}")

# User input form
with st.form("user_input_form", clear_on_submit=True):
    user_question = st.text_area("Ask a question about your documents:", height=100)
    submitted = st.form_submit_button("Send")

if submitted and user_question.strip():
    # Append user question to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    # Display a temporary thinking message
    thinking_msg = st.chat_message("assistant")
    thinking_msg.write("Thinking...")

    try:
        # Send query to backend /ask endpoint
        params = {"q": user_question}
        res = requests.get(f"{API_URL}/ask", params=params)

        if res.ok:
            data = res.json()
            answer = data.get("answer", "No answer.")
            context = data.get("context", [])

            # Update last assistant message with real answer
            thinking_msg.write(answer)

            # Append AI answer and references to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "references": context
            })
        else:
            thinking_msg.write(f"Error: {res.text}")
    except Exception as e:
        thinking_msg.write(f"Error calling backend: {e}")
