from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class QAChain:
    def __init__(self, vector_store):
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.7
        )
        self.vector_store = vector_store
        self.retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        self.chat_history = []
        
        self.prompt = PromptTemplate(
            template="""You are UniConnect, an AI assistant specialized in helping international students navigate university processes, immigration documents, and academic requirements.

Use the following context from university documents to answer the question. If you don't find the answer in the context, say so honestly but try to provide general guidance.

Context:
{context}

Question: {question}

Provide a helpful, accurate, and friendly response. If citing specific documents or policies, mention the source.""",
            input_variables=["context", "question"]
        )
    
    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    def ask(self, question: str) -> dict:
        """Ask a question and get an answer with sources."""
        # Get relevant documents
        docs = self.retriever.invoke(question)
        
        # Format context
        context = self._format_docs(docs)
        
        # Create the chain
        chain = self.prompt | self.llm | StrOutputParser()
        
        # Get answer
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        # Format sources
        sources = []
        for doc in docs:
            source_info = {
                "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "N/A")
            }
            sources.append(source_info)
        
        # Store in history
        self.chat_history.append({"question": question, "answer": answer})
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def clear_memory(self):
        """Clear conversation history."""
        self.chat_history = []
