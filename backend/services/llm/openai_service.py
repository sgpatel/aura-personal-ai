# backend/services/llm/openai_service.py
import logging
from typing import List, Dict, Any
from openai import OpenAI, APIError, RateLimitError, AsyncOpenAI # Import Async client
import asyncio # For potential sync calls in async context

from .base import LLMService
from backend.core.config import settings # Import settings to get model name

logger = logging.getLogger(__name__)

class OpenAILLMService(LLMService):
    provider = "openai"

    def __init__(self, api_key: str):
        try:
            # Use Async client for consistency with async endpoints/Ollama
            self.async_client = AsyncOpenAI(api_key=api_key)
            # self.sync_client = OpenAI(api_key=api_key) # Keep sync client if needed elsewhere
            logger.info("OpenAI Async client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            self.async_client = None

    def _handle_api_error(self, error: APIError, context: str) -> str:
        logger.error(f"OpenAI API Error ({context}): Status={error.status_code} Message={error.message}", exc_info=True)
        if isinstance(error, RateLimitError): return f"[Error: OpenAI rate limit exceeded.]"
        return f"[Error: OpenAI API request failed. {error.message}]"

    async def generate_text(self, prompt: str, max_tokens: int = 150, **kwargs) -> str:
        """Generates simple text completion using OpenAI (async)."""
        if not self.async_client: return "[Error: OpenAI client not initialized]"
        # Use configured model name
        model_name = settings.OPENAI_MODEL_NAME
        logger.info(f"Generating text with OpenAI model: {model_name}")
        try:
            response = await self.async_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                #temperature=0.7,
                **kwargs
            )
            if response.choices and response.choices[0].message:
                 return response.choices[0].message.content.strip()
            else:
                 logger.warning("OpenAI response structure unexpected or empty.")
                 return "[Error: Could not extract response from OpenAI]"
        except APIError as e: return self._handle_api_error(e, "text generation")
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI text generation: {e}", exc_info=True)
            return "[Error: An unexpected error occurred during text generation]"

    async def generate_summary(self, documents: List[str], max_tokens: int = 300, **kwargs) -> str:
        """Generates a summary from documents using OpenAI (async)."""
        if not self.async_client: return "[Error: OpenAI client not initialized]"
        if not documents: return "No documents provided for summarization."

        # Use configured model name (preferring models good at summaries like gpt-4o)
        model_name = settings.OPENAI_MODEL_NAME
        full_text = "\n\n---\n\n".join(documents)
        # TODO: Add check for token length and potentially chunk text if needed
        prompt = f"Please summarize the key points from the following document(s):\n\n{full_text}\n\nSummary:"
        logger.info(f"Generating summary with OpenAI model: {model_name}")
        try:
            response = await self.async_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
               # temperature=0.5,
                **kwargs
            )
            if response.choices and response.choices[0].message:
                 return response.choices[0].message.content.strip()
            else:
                 logger.warning("OpenAI summary response structure unexpected or empty.")
                 return "[Error: Could not extract summary from OpenAI]"
        except APIError as e: return self._handle_api_error(e, "summarization")
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI summarization: {e}", exc_info=True)
            return "[Error: An unexpected error occurred during summarization]"