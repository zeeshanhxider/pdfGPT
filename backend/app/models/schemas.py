from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PDFUploadRequest(BaseModel):
    """Request model for PDF upload."""
    pass  # File will be handled via FormData


class PDFUploadResponse(BaseModel):
    """Response model for PDF upload."""
    success: bool
    message: str
    document_id: str
    filename: str
    pages_processed: int
    chunks_created: int


class ChatMessage(BaseModel):
    """Individual chat message model."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Request model for chat queries."""
    message: str = Field(..., min_length=1, max_length=1000, description="User question")
    document_id: Optional[str] = Field(None, description="Specific document to query")
    conversation_history: List[ChatMessage] = Field(default=[], description="Previous messages in conversation")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Response creativity")
    max_tokens: int = Field(500, ge=50, le=2000, description="Maximum response length")


class ChatResponse(BaseModel):
    """Response model for chat queries."""
    success: bool
    response: str
    sources: List[str] = []
    confidence: float = 0.0
    processing_time: float = 0.0


class DocumentChunk(BaseModel):
    """Model for document chunks."""
    chunk_id: str
    document_id: str
    content: str
    page_number: int
    chunk_index: int
    metadata: dict = {}


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime
    version: str
    uptime: float
