from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from services.document_service import DocumentService
from services.chat_service import ChatService

load_dotenv()

app = FastAPI(title="Document Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_service = DocumentService()
chat_service = ChatService()


class QuestionRequest(BaseModel):
    question: str
    conversation_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]


@app.get("/")
async def root():
    return {"message": "Document Chatbot API is running"}


@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload one or more documents (PDF or text files)"""
    try:
        results = []
        for file in files:
            # Validate file type
            if not file.filename.endswith(('.pdf', '.txt')):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} must be a PDF or text file"
                )
            
            # Process document
            result = await document_service.process_document(file)
            results.append(result)
        
        return {
            "message": f"Successfully processed {len(results)} document(s)",
            "documents": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: QuestionRequest):
    """Ask a question about the uploaded documents"""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        response = await chat_service.answer_question(
            question=request.question,
            conversation_history=request.conversation_history
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents")
async def clear_documents():
    """Clear all documents from the vector store"""
    try:
        await document_service.clear_all_documents()
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pinecone_initialized": document_service.is_initialized(),
        "gemini_configured": chat_service.is_configured()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

