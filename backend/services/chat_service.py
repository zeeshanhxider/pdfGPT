from typing import List, Optional
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from services.document_service import DocumentService


class ChatService:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.gemini_api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        # Get vector store from document service
        self.document_service = DocumentService()
        self.vector_store = self.document_service.get_vector_store()
        
        # Create custom prompt template
        self.prompt_template = PromptTemplate(
            template="""You are a helpful AI assistant that answers questions based on the provided document context.
            Use the following pieces of context to answer the question at the end. 
            If you don't know the answer or if the context doesn't contain relevant information, just say that you don't have enough information to answer the question. Don't try to make up an answer.
            
            Context:
            {context}
            
            Chat History:
            {chat_history}
            
            Question: {question}
            
            Provide a helpful and accurate answer based on the context:""",
            input_variables=["context", "chat_history", "question"]
        )
    
    async def answer_question(
        self,
        question: str,
        conversation_history: Optional[List[dict]] = None
    ) -> dict:
        """Answer a question using RAG"""
        # Create retriever from vector store
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 4}  # Retrieve top 4 most relevant chunks
        )
        
        # Set up memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Add conversation history to memory
        if conversation_history:
            for msg in conversation_history[-6:]:  # Keep last 3 exchanges (6 messages)
                if msg.get("role") == "user":
                    memory.chat_memory.add_user_message(msg.get("content", ""))
                elif msg.get("role") == "assistant":
                    memory.chat_memory.add_ai_message(msg.get("content", ""))
        
        # Create conversational retrieval chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False,
            combine_docs_chain_kwargs={"prompt": self.prompt_template}
        )
        
        # Get answer
        result = qa_chain({"question": question})
        
        # Extract source information
        sources = []
        seen_sources = set()
        
        for doc in result.get("source_documents", []):
            source_name = doc.metadata.get("source", "Unknown")
            chunk_id = doc.metadata.get("chunk_id", 0)
            
            # Avoid duplicate sources
            source_key = f"{source_name}_{chunk_id}"
            if source_key not in seen_sources:
                sources.append({
                    "filename": source_name,
                    "chunk_id": chunk_id,
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
                seen_sources.add(source_key)
        
        return {
            "answer": result["answer"],
            "sources": sources
        }
    
    def is_configured(self) -> bool:
        """Check if Gemini API is configured"""
        return bool(self.gemini_api_key)

