from typing import List, Dict, Optional, Tuple
import time
import asyncio

from .pdf_processor import PDFProcessor
from .embedding_service import EmbeddingService
from .llm_service import LLMService
from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import ChatRequest, ChatResponse, PDFUploadResponse

logger = get_logger(__name__)


class RAGPipeline:
    """Main RAG (Retrieval-Augmented Generation) pipeline service."""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        logger.info("RAG Pipeline initialized")
    
    async def process_document(self, file_content: bytes, filename: str) -> PDFUploadResponse:
        """
        Process an uploaded PDF document through the complete RAG pipeline.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            
        Returns:
            PDFUploadResponse with processing results
        """
        start_time = time.time()
        
        try:
            logger.info("Starting document processing", filename=filename)
            
            # Save uploaded file
            file_path = await self.pdf_processor.save_uploaded_file(file_content, filename)
            
            try:
                # Extract text and create chunks
                document_id, chunks = await self.pdf_processor.process_pdf(file_path, filename)
                
                if not chunks:
                    return PDFUploadResponse(
                        success=False,
                        message="No text content could be extracted from the PDF",
                        document_id="",
                        filename=filename,
                        pages_processed=0,
                        chunks_created=0
                    )
                
                # Store chunks with embeddings
                success = await self.embedding_service.store_chunks(chunks)
                
                if not success:
                    return PDFUploadResponse(
                        success=False,
                        message="Failed to store document embeddings",
                        document_id=document_id,
                        filename=filename,
                        pages_processed=0,
                        chunks_created=len(chunks)
                    )
                
                # Get document statistics
                stats = await self.embedding_service.get_document_stats(document_id)
                pages_processed = stats.get("pages", 0)
                
                processing_time = time.time() - start_time
                
                logger.info(
                    "Document processing completed",
                    document_id=document_id,
                    filename=filename,
                    chunks_created=len(chunks),
                    pages_processed=pages_processed,
                    processing_time=processing_time
                )
                
                return PDFUploadResponse(
                    success=True,
                    message="Document processed successfully",
                    document_id=document_id,
                    filename=filename,
                    pages_processed=pages_processed,
                    chunks_created=len(chunks)
                )
                
            finally:
                # Clean up temporary file
                await self.pdf_processor.cleanup_file(file_path)
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "Document processing failed", 
                filename=filename, 
                error=str(e),
                processing_time=processing_time
            )
            
            return PDFUploadResponse(
                success=False,
                message=f"Failed to process document: {str(e)}",
                document_id="",
                filename=filename,
                pages_processed=0,
                chunks_created=0
            )
    
    async def answer_question(self, request: ChatRequest) -> ChatResponse:
        """
        Answer a user question using the RAG pipeline.
        
        Args:
            request: Chat request with user question and parameters
            
        Returns:
            ChatResponse with generated answer
        """
        start_time = time.time()
        
        try:
            logger.info("Processing chat query", query=request.message[:100])
            
            # Retrieve relevant chunks
            similar_chunks = await self.embedding_service.search_similar_chunks(
                query=request.message,
                document_id=request.document_id,
                k=5  # Retrieve top 5 chunks
            )
            
            # If no chunks found with document_id, try searching all documents
            if not similar_chunks and request.document_id:
                logger.info("No chunks found for specific document, searching all documents")
                similar_chunks = await self.embedding_service.search_similar_chunks(
                    query=request.message,
                    document_id=None,  # Search all documents
                    k=5
                )
            
            if not similar_chunks:
                processing_time = time.time() - start_time
                return ChatResponse(
                    success=True,
                    response="I couldn't find relevant information in the documents to answer your question. Please try rephrasing your question or upload a relevant document.",
                    sources=[],
                    confidence=0.0,
                    processing_time=processing_time
                )
            
            # Generate response using LLM
            response_text = await self.llm_service.generate_response(
                query=request.message,
                context_chunks=similar_chunks,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Extract sources and calculate confidence
            sources = self._extract_sources(similar_chunks)
            confidence = self._calculate_confidence(similar_chunks)
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Chat query processed",
                query_length=len(request.message),
                response_length=len(response_text),
                sources_count=len(sources),
                confidence=confidence,
                processing_time=processing_time
            )
            
            return ChatResponse(
                success=True,
                response=response_text,
                sources=sources,
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "Chat query processing failed",
                query=request.message[:100],
                error=str(e),
                processing_time=processing_time
            )
            
            return ChatResponse(
                success=False,
                response="I'm sorry, I encountered an error while processing your question. Please try again.",
                sources=[],
                confidence=0.0,
                processing_time=processing_time
            )
    
    def _extract_sources(self, chunks: List[Dict]) -> List[str]:
        """Extract source references from retrieved chunks."""
        sources = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown document")
            page_number = metadata.get("page_number", "unknown")
            similarity = chunk.get("similarity", 0.0)
            
            source = f"{filename} (Page {page_number}, Similarity: {similarity:.2f})"
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, chunks: List[Dict]) -> float:
        """Calculate confidence score based on chunk similarities."""
        if not chunks:
            return 0.0
        
        # Average similarity of retrieved chunks
        similarities = [chunk.get("similarity", 0.0) for chunk in chunks]
        avg_similarity = sum(similarities) / len(similarities)
        
        # Boost confidence if we have multiple high-quality chunks
        if len(chunks) >= 3 and avg_similarity > 0.8:
            confidence = min(avg_similarity * 1.1, 1.0)
        else:
            confidence = avg_similarity
        
        return round(confidence, 2)
    
    async def get_system_status(self) -> Dict:
        """Get overall system status and statistics."""
        try:
            collection_stats = await self.embedding_service.get_collection_stats()
            
            return {
                "status": "healthy",
                "vector_store": {
                    "total_chunks": collection_stats.get("total_chunks", 0),
                    "collection_name": collection_stats.get("collection_name", "unknown")
                },
                "models": {
                    "embedding_model": settings.embedding_model_name,
                    "llm_model": settings.local_llm_model_name if settings.use_local_llm else "External API",
                    "device": settings.embedding_device
                },
                "configuration": {
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap,
                    "retrieval_k": settings.retrieval_k,
                    "similarity_threshold": settings.similarity_threshold
                }
            }
            
        except Exception as e:
            logger.error("Failed to get system status", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks from the system."""
        try:
            success = await self.embedding_service.delete_document(document_id)
            logger.info("Document deletion completed", document_id=document_id, success=success)
            return success
        except Exception as e:
            logger.error("Failed to delete document", document_id=document_id, error=str(e))
            return False
