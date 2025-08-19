import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional, Tuple
import uuid
from pathlib import Path

from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import DocumentChunk

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self):
        self.model = None
        self.chroma_client = None
        self.collection = None
        self._initialize_embedding_model()
        self._initialize_vector_store()
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model."""
        try:
            logger.info("Loading embedding model", model=settings.embedding_model_name)
            self.model = SentenceTransformer(
                settings.embedding_model_name,
                device=settings.embedding_device
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store."""
        try:
            # Ensure directory exists
            Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB with persistence
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(allow_reset=True)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(
                "ChromaDB initialized",
                collection=settings.chroma_collection_name,
                persist_dir=settings.chroma_persist_directory
            )
            
        except Exception as e:
            logger.error("Failed to initialize ChromaDB", error=str(e))
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[List[float]]:
        """Generate embeddings for multiple chunks."""
        try:
            texts = [chunk.content for chunk in chunks]
            embeddings = self.model.encode(texts, convert_to_tensor=False, batch_size=32)
            return embeddings.tolist()
        except Exception as e:
            logger.error("Failed to generate embeddings for chunks", error=str(e))
            raise
    
    async def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Store document chunks with their embeddings in ChromaDB."""
        try:
            if not chunks:
                return True
            
            logger.info("Storing chunks in vector database", count=len(chunks))
            
            # Generate embeddings
            embeddings = await self.embed_chunks(chunks)
            
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                metadata = {
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
                metadatas.append(metadata)
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info("Chunks stored successfully", count=len(chunks))
            return True
            
        except Exception as e:
            logger.error("Failed to store chunks", error=str(e))
            return False
    
    async def search_similar_chunks(
        self, 
        query: str, 
        document_id: Optional[str] = None,
        k: int = None
    ) -> List[Dict]:
        """Search for similar chunks using semantic similarity."""
        try:
            k = k or settings.retrieval_k
            
            # Generate query embedding
            query_embedding = await self.embed_text(query)
            
            # Prepare where clause for filtering
            where_clause = None
            if document_id:
                where_clause = {"document_id": document_id}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            similar_chunks = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0], 
                    results["distances"][0]
                )):
                    # Convert distance to similarity score (cosine distance -> similarity)
                    similarity = 1 - distance
                    
                    if similarity >= settings.similarity_threshold:
                        similar_chunks.append({
                            "content": doc,
                            "metadata": metadata,
                            "similarity": similarity,
                            "rank": i + 1
                        })
            
            logger.info(
                "Similar chunks retrieved",
                query_length=len(query),
                total_results=len(similar_chunks),
                document_id=document_id
            )
            
            return similar_chunks
            
        except Exception as e:
            logger.error("Failed to search similar chunks", error=str(e))
            return []
    
    async def get_document_stats(self, document_id: str) -> Dict:
        """Get statistics for a specific document."""
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if not results["metadatas"]:
                return {"chunks": 0, "pages": 0}
            
            metadatas = results["metadatas"]
            pages = set()
            
            for metadata in metadatas:
                pages.add(metadata.get("page_number", 0))
            
            return {
                "chunks": len(metadatas),
                "pages": len(pages),
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error("Failed to get document stats", document_id=document_id, error=str(e))
            return {"chunks": 0, "pages": 0}
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a specific document."""
        try:
            # Get all chunks for the document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["ids"]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info("Document deleted from vector store", document_id=document_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to delete document", document_id=document_id, error=str(e))
            return False
    
    async def get_collection_stats(self) -> Dict:
        """Get overall collection statistics."""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": settings.chroma_collection_name
            }
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {"total_chunks": 0}
