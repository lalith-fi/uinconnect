# UniConnect - AI Platform for International Student Guidance

An AI-powered document search system using LangChain to help students navigate academic and immigration documents through intelligent Q&A.

## Features

- **PDF Document Processing** - Upload and process university documents, forms, and policies
- **Semantic Search** - FAISS vector database for accurate document retrieval
- **Intelligent Q&A** - GPT-4o-mini powered contextual answers from your documents
- **Source Citations** - View exact sources and page numbers for every answer
- **User Authentication** - Supabase-powered login/registration system
- **Role-Based Access** - Admin-only document upload, all users can ask questions
- **Persistent Vector Store** - Processed documents saved for fast subsequent loads
- **Conversation Memory** - Context-aware follow-up questions

## Tech Stack

- **LangChain** - Document processing & QA chain
- **FAISS** - Vector similarity search
- **OpenAI GPT-4o-mini** - Answer generation
- **OpenAI Embeddings** - Document vectorization
- **Streamlit** - Web interface
- **Supabase** - Authentication & user management
