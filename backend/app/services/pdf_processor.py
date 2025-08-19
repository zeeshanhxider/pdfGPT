import pdfplumber
import PyPDF2
from typing import List, Dict, Tuple
import uuid
import os
from pathlib import Path
import re

from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import DocumentChunk

logger = get_logger(__name__)


class PDFProcessor:
    """Service for processing PDF documents."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_pdf(self, file_path: str, filename: str) -> Tuple[str, List[DocumentChunk]]:
        """
        Process a PDF file and extract text chunks.
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            
        Returns:
            Tuple of (document_id, list of chunks)
        """
        document_id = str(uuid.uuid4())
        logger.info("Processing PDF", filename=filename, document_id=document_id)
        
        try:
            # Extract text from PDF
            text_content = await self._extract_text_from_pdf(file_path)
            
            # Split text into chunks
            chunks = await self._create_chunks(text_content, document_id, filename)
            
            logger.info(
                "PDF processed successfully",
                document_id=document_id,
                total_chunks=len(chunks),
                total_chars=len(text_content)
            )
            
            return document_id, chunks
            
        except Exception as e:
            logger.error("Failed to process PDF", filename=filename, error=str(e))
            raise
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber with PyPDF2 fallback."""
        text_content = ""
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
            
            if not text_content.strip():
                # Fallback to PyPDF2
                logger.info("pdfplumber returned empty text, trying PyPDF2")
                text_content = await self._extract_with_pypdf2(file_path)
                
        except Exception as e:
            logger.warning("pdfplumber failed, trying PyPDF2", error=str(e))
            text_content = await self._extract_with_pypdf2(file_path)
        
        return text_content
    
    async def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2 as fallback."""
        text_content = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
        
        return text_content
    
    async def _create_chunks(self, text: str, document_id: str, filename: str) -> List[DocumentChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split by pages first
        pages = text.split("--- Page ")
        
        chunk_index = 0
        for page_idx, page_content in enumerate(pages):
            if not page_content.strip():
                continue
                
            page_number = page_idx
            if page_content.startswith("---"):
                # Extract page number from marker
                try:
                    page_number = int(page_content.split("---")[0].strip())
                    page_content = "---".join(page_content.split("---")[1:])
                except:
                    page_number = page_idx
            
            # Split page into chunks
            page_chunks = self._split_text_into_chunks(page_content)
            
            for chunk_text in page_chunks:
                if len(chunk_text.strip()) < 50:  # Skip very short chunks
                    continue
                
                chunk = DocumentChunk(
                    chunk_id=f"{document_id}_{chunk_index}",
                    document_id=document_id,
                    content=chunk_text.strip(),
                    page_number=page_number,
                    chunk_index=chunk_index,
                    metadata={
                        "filename": filename,
                        "chunk_length": len(chunk_text),
                        "page_number": page_number
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\-.,!?;:()\[\]{}"]', ' ', text)
        
        return text.strip()
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            chunk = text[start:end]
            last_period = chunk.rfind('.')
            last_question = chunk.rfind('?')
            last_exclamation = chunk.rfind('!')
            
            break_point = max(last_period, last_question, last_exclamation)
            
            if break_point > start + chunk_size // 2:  # Only break if we're past halfway
                end = start + break_point + 1
            
            chunks.append(text[start:end])
            start = max(start + chunk_size - overlap, end - overlap)
        
        return chunks
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk and return file path."""
        # Generate unique filename to avoid conflicts
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix
        unique_filename = f"{file_id}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info("File saved", original_filename=filename, saved_path=str(file_path))
        return str(file_path)
    
    async def cleanup_file(self, file_path: str) -> None:
        """Clean up temporary files."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("File cleaned up", file_path=file_path)
        except Exception as e:
            logger.warning("Failed to cleanup file", file_path=file_path, error=str(e))
