from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from ..models.schemas import (
    PDFUploadResponse, 
    ChatRequest, 
    ChatResponse,
    HealthResponse
)
from ..services.rag_pipeline import RAGPipeline
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Global RAG pipeline instance
rag_pipeline = RAGPipeline()


@router.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database status."""
    try:
        collection = rag_pipeline.embedding_service.collection
        total_count = collection.count()
        
        # Get a sample of documents
        sample_result = collection.get(
            limit=5,
            include=["documents", "metadatas"]
        )
        
        return {
            "total_chunks": total_count,
            "sample_documents": sample_result.get("documents", [])[:2],  # First 2 for brevity
            "sample_metadatas": sample_result.get("metadatas", [])[:2],
            "similarity_threshold": settings.similarity_threshold
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    
    The uploaded PDF will be processed to extract text, create chunks,
    generate embeddings, and store them in the vector database.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {settings.max_file_size // (1024*1024)}MB"
        )
    
    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    logger.info("Processing PDF upload", filename=file.filename, size=len(file_content))
    
    try:
        # Process the document
        result = await rag_pipeline.process_document(file_content, file.filename)
        
        if result.success:
            logger.info("PDF uploaded successfully", 
                       document_id=result.document_id, 
                       filename=result.filename)
        else:
            logger.warning("PDF upload failed", 
                          filename=result.filename, 
                          message=result.message)
        
        return result
        
    except Exception as e:
        logger.error("PDF upload error", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask a question about uploaded documents.
    
    Uses retrieval-augmented generation to find relevant content
    and generate contextual answers.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    logger.info("Processing chat request", 
                message_length=len(request.message),
                document_id=request.document_id)
    
    try:
        response = await rag_pipeline.answer_question(request)
        
        if response.success:
            logger.info("Chat response generated", 
                       response_length=len(response.response),
                       sources_count=len(response.sources),
                       confidence=response.confidence)
        
        return response
        
    except Exception as e:
        logger.error("Chat error", message=request.message[:100], error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@router.post("/debug/chat")
async def debug_chat(request: dict):
    """Debug chat endpoint that searches all documents."""
    try:
        query = request.get("message", "")
        
        # Search without document_id filtering
        similar_chunks = await rag_pipeline.embedding_service.search_similar_chunks(
            query=query,
            document_id=None,  # Search all documents
            k=5
        )
        
        return {
            "query": query,
            "chunks_found": len(similar_chunks),
            "chunks": similar_chunks[:2] if similar_chunks else [],  # Show first 2
            "similarity_threshold": settings.similarity_threshold
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/debug/full-chat")
async def debug_full_chat(request: ChatRequest):
    """Debug endpoint that mimics the full chat flow."""
    try:
        # Use the exact same flow as regular chat
        response = await rag_pipeline.answer_question(request)
        return {
            "original_request": {
                "message": request.message,
                "document_id": request.document_id
            },
            "response": response.dict(),
            "debug_info": {
                "similarity_threshold": settings.similarity_threshold
            }
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.version,
        uptime=time.time()  # Simple uptime placeholder
    )


@router.get("/status")
async def get_system_status():
    """Get detailed system status and statistics."""
    try:
        status = await rag_pipeline.get_system_status()
        return status
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document and all its chunks."""
    try:
        success = await rag_pipeline.delete_document(document_id)
        
        if success:
            return {"success": True, "message": "Document deleted successfully"}
        else:
            return {"success": False, "message": "Document not found or deletion failed"}
            
    except Exception as e:
        logger.error("Failed to delete document", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document")
