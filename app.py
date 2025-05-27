import streamlit as st
import os
import shutil
import json
import time
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
from pathlib import Path
from langsmith import Client
from rag_pipeline.embedder import initialize_embeddings, initialize_llm
from rag_pipeline.weviate_helper import initialize_weaviate, create_or_connect_class
from rag_pipeline.file_loader import load_documents, split_documents
from rag_pipeline.rag_pipeline import store_embeddings, initialize_prompt, query_rag

load_dotenv()

# Initialize LangSmith client
langsmith_client = Client()

# Validate environment variables
required_env_vars = ["GOOGLE_API_KEY", "WEAVIATE_URL", "WEAVIATE_API_KEY", "LANGCHAIN_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    st.error(f"Missing environment variables: {', '.join(missing_vars)}. Please check .env file.")
    st.stop()

# Initialize Streamlit app
st.set_page_config(page_title="DocQuery Chat", page_icon="📚", layout="wide")

# Custom CSS for chatbot-style UI
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stSidebar { background-color: rgb(66,64,64); border-right: 1px solid #e0e0e0; }
    .chat-message-user { padding: 12px; border-radius: 12px; margin: 8px 0; max-width: 80%; background-color: #007bff; color: white; margin-left: auto; }
    .chat-message-assistant { padding: 12px; border-radius: 12px; margin: 8px 0; max-width: 80%; background-color: #28a745; color: white; margin-right: auto; }
    .chat-container { height: 60vh; overflow-y: auto; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: white; }
    .stTextInput { position: sticky; bottom: 0; background-color: white; padding: 10px; }
    .stButton>button { background-color: #007bff; color: white; border-radius: 8px; }
    .stButton>button:hover { background-color: #0056b3; }
    .file-info { font-size: 0.9em; color: #555; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "weaviate_client" not in st.session_state:
    st.session_state.weaviate_client = None
if "prompt_template" not in st.session_state:
    st.session_state.prompt_template = None
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()

# Create temporary directory for uploaded files
TEMP_DIR = "temp_uploads"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def clear_temp_dir():
    """Remove all files in the temporary directory."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)

def cleanup():
    """Close Weaviate client and clear session state."""
    if st.session_state.weaviate_client is not None:
        print("Closing Weaviate client...")
        st.session_state.weaviate_client.close()
        st.session_state.weaviate_client = None
    st.session_state.vector_store = None
    st.session_state.prompt_template = None
    st.session_state.chat_history = []
    st.session_state.authenticated = False
    clear_temp_dir()
    st.success("Session cleared and resources cleaned up.")

def validate_filename(filename):
    """Sanitize and validate filename to prevent path traversal."""
    safe_filename = Path(filename).name
    if not safe_filename.endswith((".pdf", ".docx", ".txt")):
        return None
    return safe_filename

def process_documents(uploaded_files):
    """Process uploaded documents and store embeddings in Weaviate."""
    st.session_state.last_activity = time.time()
    if not uploaded_files:
        st.error("Please upload at least one document.")
        return
    if len(uploaded_files) > 50:
        st.warning("Uploading more than 50 documents may cause performance issues. Consider processing in batches.")
        return

    # Save uploaded files to temporary directory
    file_paths = []
    total_size = 0
    for uploaded_file in uploaded_files:
        safe_filename = validate_filename(uploaded_file.name)
        if not safe_filename:
            st.error(f"Invalid file type: {uploaded_file.name}. Supported: PDF, DOCX, TXT.")
            continue
        file_path = os.path.join(TEMP_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append(file_path)
        total_size += uploaded_file.size
    if total_size > 200 * 1024 * 1024:  # 200 MB
        st.error("Total file size exceeds 200 MB. Please upload fewer or smaller files.")
        clear_temp_dir()
        return

    try:
        with st.spinner("Initializing embeddings and LLM..."):
            embeddings = initialize_embeddings()
            llm = initialize_llm()

        with st.spinner("Initializing Weaviate..."):
            if st.session_state.weaviate_client is None:
                st.session_state.weaviate_client = initialize_weaviate()
            collection = create_or_connect_class(st.session_state.weaviate_client, class_name="Document")

        with st.spinner("Loading and splitting documents..."):
            documents = load_documents(file_paths)
            if not documents:
                st.error("No valid documents loaded.")
                return
            st.markdown(f"<div class='file-info'>Loaded {len(documents)} document(s): {[Path(fp).name for fp in file_paths]}</div>", unsafe_allow_html=True)
            chunks = split_documents(documents)
            if not chunks:
                st.error("No document chunks created.")
                return

        with st.spinner("Generating and storing embeddings..."):
            st.session_state.vector_store = store_embeddings(
                chunks, collection.name, st.session_state.weaviate_client, embeddings
            )

        with st.spinner("Initializing prompt..."):
            st.session_state.prompt_template = initialize_prompt()

        st.success("Documents processed successfully! You can now ask questions.")
    except Exception as e:
        st.error(f"Error processing documents: {e}")
    finally:
        clear_temp_dir()

# Authentication
if not st.session_state.authenticated:
    st.header("Login to DocQuery Chat")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
            if username in users and sha256_crypt.verify(password, users[username]):
                st.session_state.authenticated = True
                st.session_state.last_activity = time.time()
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        except FileNotFoundError:
            st.error("User database not found. Please contact the administrator.")
        except Exception as e:
            st.error(f"Login error: {e}")
else:
    # Check for session timeout (30 minutes)
    if time.time() - st.session_state.last_activity > 1800:
        cleanup()
        st.error("Session timed out. Please log in again.")
        st.rerun()

    # Main app
    st.header("📚 DocQuery Chat")
    st.markdown("Chat with your documents in a secure, conversational interface.")

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        st.markdown("Upload up to 50 documents (PDF, DOCX, TXT), total size <200 MB.")
        uploaded_files = st.file_uploader(
            "Upload PDF, DOCX, or TXT files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        if st.button("Process Documents"):
            process_documents(uploaded_files)
        if st.button("Clear Session"):
            cleanup()
            st.rerun()
        if st.button("Logout"):
            cleanup()
            st.rerun()

    # Chat interface
    st.subheader("Chat")
    if st.session_state.vector_store is None:
        st.info("Please upload and process documents to start chatting.")
    else:
        # Chat container
        chat_container = st.container()
        with chat_container:
            for idx, message in enumerate(st.session_state.chat_history):
                css_class = "chat-message-user" if message["role"] == "user" else "chat-message-assistant"
                st.markdown(f"<div class='{css_class}'>{message['content']}</div>", unsafe_allow_html=True)
                
                # Show feedback UI for the latest assistant message, or display finalized feedback for past messages
                if message["role"] == "assistant":
                    # Check if this is the latest assistant message (i.e., the last message in chat_history)
                    is_latest_message = idx == len(st.session_state.chat_history) - 1
                    if is_latest_message:
                        # Display feedback options with a submit button
                        feedback_key = f"feedback_{idx}"
                        default_feedback = message.get("feedback", None)
                        feedback = st.radio(
                            "Was this response helpful?",
                            ("👍 Yes", "👎 No"),
                            key=feedback_key,
                            horizontal=True,
                            index=None if default_feedback is None else (0 if default_feedback == "👍 Yes" else 1)
                        )

                        if st.button("Submit Feedback", key=f"submit_feedback_{idx}"):
                            if feedback is None:
                                st.warning("Please select a feedback option before submitting.")
                            elif message.get("run_id"):
                                feedback_score = 1 if feedback == "👍 Yes" else 0
                                langsmith_client.create_feedback(
                                    run_id=message["run_id"],
                                    key="user-feedback",
                                    score=feedback_score,
                                    comment=f"User feedback for message {idx}"
                                )
                                message["feedback"] = feedback
                                st.rerun()
                            else:
                                st.error("Unable to log feedback: No LangSmith run ID found.")

                        # Display the current feedback if it exists
                        if "feedback" in message:
                            st.markdown(f"**Current Feedback:** {message['feedback']}", unsafe_allow_html=True)
                    else:
                        # For past messages, display finalized feedback if it exists
                        if "feedback" in message:
                            st.markdown(f"**Feedback:** {message['feedback']}", unsafe_allow_html=True)

        # Chat input
        if question := st.chat_input("Ask a question about the documents"):
            st.session_state.last_activity = time.time()
            st.session_state.chat_history.append({"role": "user", "content": question})
            with chat_container:
                st.markdown(f"<div class='chat-message-user'>{question}</div>", unsafe_allow_html=True)
                with st.spinner("Processing..."):
                    try:
                        # Get the latest run ID before calling query_rag
                        runs = list(langsmith_client.list_runs(project_name="DocQuery-Chat-Eval", limit=1))
                        pre_run_id = runs[0].id if runs else None

                        # Query the RAG system
                        answer = query_rag(
                            question,
                            st.session_state.vector_store,
                            initialize_llm(),
                            st.session_state.prompt_template
                        )

                        # Get the latest run ID after the query
                        runs = list(langsmith_client.list_runs(project_name="DocQuery-Chat-Eval", limit=1))
                        post_run_id = runs[0].id if runs else None

                        # Store the run ID with the message
                        assistant_message = {
                            "role": "assistant",
                            "content": answer,
                            "run_id": post_run_id if pre_run_id != post_run_id else None
                        }
                        st.session_state.chat_history.append(assistant_message)
                        st.rerun()  # Rerun to render the new message via the chat_history loop

                    except Exception as e:
                        st.error(f"Error generating answer: {e}")
                        st.session_state.chat_history.append({"role": "assistant", "content": f"Error: {e}"})
                        st.rerun()