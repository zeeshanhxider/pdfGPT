from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from typing import List, Dict, Optional
import httpx
import asyncio
import time

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for generating responses using language models."""
    
    def __init__(self):
        self.local_model = None
        self.tokenizer = None
        if settings.use_local_llm:
            self._initialize_local_model()
    
    def _initialize_local_model(self):
        """Initialize local LLM model."""
        try:
            logger.info("Loading local LLM model", model=settings.local_llm_model_name)
            
            # For a more capable but smaller model, we'll use a text generation pipeline
            self.local_model = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium",
                device=0 if torch.cuda.is_available() else -1,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            logger.info("Local LLM model loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load local LLM model", error=str(e))
            self.local_model = None

    async def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate a response using the available LLM."""
        
        # Try external APIs first (better quality)
        if settings.cohere_api_key or settings.openai_api_key or settings.anthropic_api_key:
            try:
                return await self._generate_with_external_api(
                    query, context_chunks, temperature, max_tokens
                )
            except Exception as e:
                logger.warning("External API failed, falling back to local model", error=str(e))
        
        # Use local model as fallback
        if settings.use_local_llm and self.local_model:
            return await self._generate_with_local_model(
                query, context_chunks, temperature, max_tokens
            )
        else:
            # Final fallback to rule-based response
            return self._generate_fallback_response(query, context_chunks)

    async def _generate_with_local_model(
        self,
        query: str,
        context_chunks: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response using local model."""
        try:
            # Create context from retrieved chunks
            context = self._format_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(query, context)
            
            # Generate response
            start_time = time.time()
            
            response = self.local_model(
                prompt,
                max_length=len(prompt.split()) + max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.local_model.tokenizer.eos_token_id,
                num_return_sequences=1,
                truncation=True
            )
            
            generation_time = time.time() - start_time
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            
            # Remove the prompt from the response
            if prompt in generated_text:
                answer = generated_text.replace(prompt, "").strip()
            else:
                answer = generated_text.strip()
            
            # Clean up the response
            answer = self._clean_response(answer)
            
            # If answer is empty or too short, use fallback
            if not answer or len(answer.strip()) < 10:
                logger.warning("Generated answer is empty or too short, using fallback")
                return self._generate_fallback_response(query, context_chunks)
            
            logger.info(
                "Local model response generated",
                generation_time=generation_time,
                response_length=len(answer)
            )
            
            return answer
            
        except Exception as e:
            logger.error("Failed to generate response with local model", error=str(e))
            return self._generate_fallback_response(query, context_chunks)

    async def _generate_with_external_api(
        self,
        query: str,
        context_chunks: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response using external API (Cohere, OpenAI, or Anthropic)."""
        
        context = self._format_context(context_chunks)
        
        if settings.cohere_api_key:
            return await self._call_cohere_api(query, context, temperature, max_tokens)
        elif settings.openai_api_key:
            return await self._call_openai_api(query, context, temperature, max_tokens)
        elif settings.anthropic_api_key:
            return await self._call_anthropic_api(query, context, temperature, max_tokens)
        else:
            raise Exception("No external API key configured")

    async def _call_cohere_api(
        self, query: str, context: str, temperature: float, max_tokens: int
    ) -> str:
        """Call Cohere API for text generation."""
        headers = {
            "Authorization": f"Bearer {settings.cohere_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Based on the following context, please answer the question accurately and concisely.

Context:
{context}

Question: {query}

Answer:"""

        data = {
            "model": "command-r-plus",  # Cohere's latest model
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "truncate": "END"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.cohere.ai/v1/generate",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result["generations"][0]["text"].strip()

    async def _call_openai_api(
        self, query: str, context: str, temperature: float, max_tokens: int
    ) -> str:
        """Call OpenAI API."""
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context. Use only the information from the context to answer questions."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"}
        ]
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

    async def _call_anthropic_api(
        self, query: str, context: str, temperature: float, max_tokens: int
    ) -> str:
        """Call Anthropic API."""
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        prompt = f"""Based on the following context, please answer the question accurately and concisely.

Context:
{context}

Question: {query}

Answer:"""
        
        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"].strip()

    def _format_context(self, context_chunks: List[Dict]) -> str:
        """Format context chunks into a coherent context string."""
        if not context_chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            content = chunk["content"]
            metadata = chunk.get("metadata", {})
            page_num = metadata.get("page_number", "unknown")
            
            context_parts.append(f"[Source {i} - Page {page_num}]\n{content}")
        
        return "\n\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create a prompt for the language model."""
        return f"""Based on the following context, please answer the question accurately and concisely.

Context:
{context}

Question: {query}

Answer:"""

    def _clean_response(self, response: str) -> str:
        """Clean up the generated response."""
        # Remove common artifacts
        response = response.replace("Assistant:", "").replace("AI:", "").strip()
        
        # Remove repetitive text (common in smaller models)
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and line not in cleaned_lines[-3:]:  # Avoid immediate repetition
                cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines)
        
        # Limit response length if too long
        if len(response) > 1000:
            response = response[:1000] + "..."
        
        return response

    def _generate_fallback_response(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate a simple fallback response when models are unavailable."""
        if not context_chunks:
            return "I couldn't find relevant information in the document to answer your question."
        
        # Create a response based on the most relevant chunks
        relevant_info = []
        for i, chunk in enumerate(context_chunks[:2]):  # Use top 2 chunks
            content = chunk["content"]
            # Truncate if too long
            if len(content) > 200:
                content = content[:200] + "..."
            relevant_info.append(content)
        
        combined_content = " ".join(relevant_info)
        
        # Generate a simple response based on the query type
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["what", "about", "describe", "summary", "summarize"]):
            return f"Based on the document, this appears to be about: {combined_content}"
        elif any(word in query_lower for word in ["when", "time", "date", "schedule"]):
            return f"According to the document: {combined_content}"
        elif any(word in query_lower for word in ["where", "location", "place"]):
            return f"The document mentions: {combined_content}"
        elif any(word in query_lower for word in ["who", "person", "people"]):
            return f"From the document: {combined_content}"
        elif any(word in query_lower for word in ["how", "process", "method"]):
            return f"The document explains: {combined_content}"
        else:
            return f"Based on your question about '{query}', here's what I found in the document: {combined_content}"