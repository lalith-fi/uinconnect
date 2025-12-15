import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from src.document_processor import DocumentProcessor
from src.qa_chain import QAChain

# Load environment variables
load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# Page config
st.set_page_config(
    page_title="UniConnect",
    page_icon="🎓",
    layout="centered"
)

# Minimal clean CSS + Font Awesome
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    .block-container {
        padding-top: 2rem;
    }
    .role-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .admin-badge {
        background-color: #fee2e2;
        color: #dc2626;
    }
    .user-badge {
        background-color: #dbeafe;
        color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processor" not in st.session_state:
    st.session_state.processor = DocumentProcessor()
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "user" not in st.session_state:
    st.session_state.user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None


def get_user_profile(user_id: str) -> dict:
    """Get user profile from Supabase."""
    try:
        response = supabase.table("user_profiles").select("role, first_name, last_name").eq("id", user_id).single().execute()
        if response.data:
            first = response.data.get("first_name", "")
            last = response.data.get("last_name", "")
            return {
                "role": response.data.get("role", "user"),
                "first_name": first,
                "last_name": last,
                "full_name": f"{first} {last}".strip()
            }
    except:
        pass
    return {"role": "user", "first_name": "", "last_name": "", "full_name": ""}


def login(email: str, password: str) -> bool:
    """Authenticate user with Supabase."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            st.session_state.user = response.user
            profile = get_user_profile(response.user.id)
            st.session_state.user_role = profile["role"]
            st.session_state.user_name = profile["full_name"]
            return True
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
    return False


def register(email: str, password: str, first_name: str, last_name: str) -> bool:
    """Register new user with Supabase."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            supabase.table("user_profiles").update({
                "first_name": first_name,
                "last_name": last_name
            }).eq("id", response.user.id).execute()
            st.success("Registration successful! You can now login.")
            return True
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")
    return False


def logout():
    """Log out user."""
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.messages = []


def initialize_qa_system():
    """Initialize or load the QA system."""
    processor = st.session_state.processor
    vector_store = processor.load_vector_store()
    if vector_store:
        st.session_state.qa_chain = QAChain(vector_store)
        st.session_state.documents_loaded = True
        return True
    return False


def process_documents():
    """Process all PDFs in the data directory."""
    processor = st.session_state.processor
    with st.spinner("Processing documents..."):
        documents = processor.load_pdfs()
        if not documents:
            st.warning("No PDF documents found in data/pdfs folder.")
            return False
        chunks = processor.split_documents(documents)
        processor.create_vector_store(chunks)
        processor.save_vector_store()
        st.session_state.qa_chain = QAChain(processor.vector_store)
        st.session_state.documents_loaded = True
        st.success(f"Processed {len(documents)} documents!")
        return True


# Check Supabase
if not supabase:
    st.error("Supabase not configured! Add credentials to .env file.")
    st.stop()

# ==================== LOGIN PAGE ====================
if not st.session_state.user:
    st.markdown("<h1><i class='fa-solid fa-graduation-cap'></i> UniConnect</h1>", unsafe_allow_html=True)
    st.caption("AI-Powered Guide for International Students")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True, type="primary"):
            if login(login_email, login_password):
                st.rerun()
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            reg_first_name = st.text_input("First Name", key="reg_first_name")
        with col2:
            reg_last_name = st.text_input("Last Name", key="reg_last_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_password2 = st.text_input("Confirm Password", type="password", key="reg_password2")
        
        if st.button("Register", use_container_width=True, type="primary"):
            if not reg_first_name or not reg_last_name:
                st.error("Please enter your name!")
            elif reg_password != reg_password2:
                st.error("Passwords don't match!")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters!")
            else:
                register(reg_email, reg_password, reg_first_name, reg_last_name)

# ==================== MAIN APP ====================
else:
    # Sidebar
    with st.sidebar:
        st.markdown("<h2><i class='fa-solid fa-graduation-cap'></i> UniConnect</h2>", unsafe_allow_html=True)
        
        # User info
        display_name = st.session_state.user_name or st.session_state.user.email
        st.markdown(f"<i class='fa-solid fa-user'></i> **{display_name}**", unsafe_allow_html=True)
        
        role_class = "admin-badge" if st.session_state.user_role == "admin" else "user-badge"
        st.markdown(f'<span class="role-badge {role_class}">{st.session_state.user_role.upper()}</span>', unsafe_allow_html=True)
        
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
        
        st.divider()
        
        # Admin: Document Management
        if st.session_state.user_role == "admin":
            st.markdown("<h4><i class='fa-solid fa-folder-open'></i> Document Management</h4>", unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "Upload PDF Documents",
                type="pdf",
                accept_multiple_files=True
            )
            
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_path = os.path.join("data/pdfs", uploaded_file.name)
                    os.makedirs("data/pdfs", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"Uploaded: {uploaded_file.name}")
            
            if st.button("Process Documents", use_container_width=True, type="primary"):
                process_documents()
            
            st.divider()
        
        # Status
        if st.session_state.documents_loaded:
            st.success("Documents ready!")
        else:
            st.warning("Waiting for documents...")
        
        st.divider()
        
        # Sample questions
        st.markdown("<h4><i class='fa-solid fa-lightbulb'></i> Try asking</h4>", unsafe_allow_html=True)
        questions = [
            "F-1 visa requirements?",
            "How to apply for OPT?",
            "I-20 documents needed?",
        ]
        for q in questions:
            if st.button(q, key=q, use_container_width=True):
                st.session_state.pending_question = q
        
        if st.button("Clear Chat", use_container_width=True, icon=":material/delete:"):
            st.session_state.messages = []
            if st.session_state.qa_chain:
                st.session_state.qa_chain.clear_memory()
            st.rerun()

    # Main content
    first_name = st.session_state.user_name.split()[0] if st.session_state.user_name else "there"
    st.markdown(f"<h1>Hi {first_name}!</h1>", unsafe_allow_html=True)
    st.caption("Ask me anything about university processes, visa requirements, or academic policies.")
    
    st.divider()
    
    # Initialize QA
    if not st.session_state.documents_loaded:
        initialize_qa_system()

    # Chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"**Source {i}:** {source['source']} (Page {source['page']})")
                        st.caption(source['content'][:200] + "...")

    # Handle pending question
    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question
        if st.session_state.qa_chain:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Thinking..."):
                response = st.session_state.qa_chain.ask(question)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"]
            })
            st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask your question..."):
        if not st.session_state.documents_loaded:
            st.error("Please wait for documents to be loaded.")
        elif not st.session_state.qa_chain:
            st.error("QA system initializing...")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Searching..."):
                    response = st.session_state.qa_chain.ask(prompt)
                st.write(response["answer"])
                if response["sources"]:
                    with st.expander("Sources"):
                        for i, source in enumerate(response["sources"], 1):
                            st.markdown(f"**Source {i}:** {source['source']} (Page {source['page']})")
                            st.caption(source['content'][:200] + "...")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"]
            })
