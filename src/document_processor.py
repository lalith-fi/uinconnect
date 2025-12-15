import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class DocumentProcessor:
    def __init__(self, pdf_directory: str = "data/pdfs"):
        self.pdf_directory = pdf_directory
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.vector_store_path = "data/vector_store"
    
    def load_pdfs(self) -> list:
        """Load all PDFs from the directory."""
        if not os.path.exists(self.pdf_directory):
            os.makedirs(self.pdf_directory)
            return []
        
        loader = DirectoryLoader(
            self.pdf_directory,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True
        )
        documents = loader.load()
        return documents
    
    def split_documents(self, documents: list) -> list:
        """Split documents into chunks for better retrieval."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        return chunks
    
    def create_vector_store(self, chunks: list) -> FAISS:
        """Create FAISS vector store from document chunks."""
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        return self.vector_store
    
    def save_vector_store(self):
        """Save vector store to disk."""
        if self.vector_store:
            self.vector_store.save_local(self.vector_store_path)
    
    def load_vector_store(self) -> FAISS:
        """Load existing vector store from disk."""
        if os.path.exists(self.vector_store_path):
            self.vector_store = FAISS.load_local(
                self.vector_store_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            return self.vector_store
        return None
    
    def process_new_pdf(self, pdf_path: str):
        """Process a single new PDF and add to vector store."""
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        chunks = self.split_documents(documents)
        
        if self.vector_store:
            self.vector_store.add_documents(chunks)
        else:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        self.save_vector_store()
        return len(chunks)
    
    def get_relevant_documents(self, query: str, k: int = 4) -> list:
        """Retrieve relevant document chunks for a query."""
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k)

