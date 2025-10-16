import io
import tempfile
from typing import List
from fastapi import UploadFile
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import os
import uuid


class DocumentService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize Pinecone
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "document-chatbot")
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self._initialize_index()
        
        # Initialize vector store
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def _initialize_index(self):
        """Create Pinecone index if it doesn't exist"""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # Dimension for all-MiniLM-L6-v2
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
    
    async def process_document(self, file: UploadFile) -> dict:
        """Extract text from document and store in vector database"""
        # Extract text based on file type
        if file.filename.endswith('.pdf'):
            text = await self._extract_text_from_pdf(file)
        else:  # .txt file
            content = await file.read()
            text = content.decode('utf-8')
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create metadata for each chunk
        metadatas = [
            {
                "source": file.filename,
                "chunk_id": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]
        
        # Generate unique IDs for each chunk
        ids = [f"{file.filename}_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(chunks))]
        
        # Add to vector store
        self.vector_store.add_texts(
            texts=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "filename": file.filename,
            "chunks": len(chunks),
            "total_characters": len(text)
        }
    
    async def _extract_text_from_pdf(self, file: UploadFile) -> str:
        """Extract text from PDF file"""
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    
    async def clear_all_documents(self):
        """Clear all documents from the vector store"""
        # Delete and recreate the index
        self.pc.delete_index(self.index_name)
        self._initialize_index()
        
        # Reinitialize vector store
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )
    
    def is_initialized(self) -> bool:
        """Check if Pinecone is properly initialized"""
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            return self.index_name in existing_indexes
        except:
            return False
    
    def get_vector_store(self):
        """Get the vector store instance"""
        return self.vector_store

