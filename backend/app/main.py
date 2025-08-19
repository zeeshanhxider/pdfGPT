from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .api.endpoints import router as api_router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="A production-grade RAG system for PDF document Q&A",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include API router
app.include_router(api_router, prefix="/api/v1", tags=["RAG API"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting PDF ChatBot RAG API", version=settings.version)
    

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down PDF ChatBot RAG API")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PDF ChatBot RAG API",
        "version": settings.version,
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
