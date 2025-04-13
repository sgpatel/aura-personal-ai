# backend/services/llm/gemini_service.py
import logging
from typing import List, Dict, Any
import google.generativeai as genai
import asyncio # For running sync code in async context if needed

from .base import LLMService
from backend.core.config import settings

logger = logging.getLogger(__name__)

class GeminiLLMService(LLMService):
    provider = "gemini"

    def __init__(self, api_key: str):
        try:
            genai.configure(api_key=api_key)
            # TODO: Potentially configure model name from settings
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info(f"Google Generative AI client configured for model: {self.model.model_name}")
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI: {e}", exc_info=True)
            self.model = None

    def _handle_api_error(self, error: Exception, context: str) -> str:
        logger.error(f"Google Gemini API Error ({context}): {error}", exc_info=True)
        return f"[Error: Google Gemini API request failed. {error}]"

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generates simple text completion using Gemini (async wrapper)."""
        if not self.model: return "[Error: Google Gemini client not initialized]"
        logger.info(f"Generating text with Google Gemini model: {self.model.model_name}")
        try:
            # The core generate_content might be sync, run in threadpool
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            # response = self.model.generate_content(prompt) # If library becomes async native
            if response.parts: return response.text
            elif response.prompt_feedback.block_reason:
                 logger.warning(f"Gemini blocked: {response.prompt_feedback.block_reason}")
                 return f"[Content blocked: {response.prompt_feedback.block_reason}]"
            else: logger.warning("Gemini response empty."); return "[Error: No text generated]"
        except Exception as e: return self._handle_api_error(e, "text generation")

    async def generate_summary(self, documents: List[str], **kwargs) -> str:
        """Generates a summary from documents using Gemini (async wrapper)."""
        if not self.model: return "[Error: Google Gemini client not initialized]"
        if not documents: return "No documents provided for summarization."
        full_text = "\n\n---\n\n".join(documents)
        prompt = f"Summarize the following document(s):\n\n{full_text}\n\nSummary:"
        logger.info(f"Generating summary with Google Gemini model: {self.model.model_name}")
        try:
            # Run sync call in threadpool
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            # response = self.model.generate_content(prompt) # If library becomes async native
            if response.parts: return response.text
            elif response.prompt_feedback.block_reason:
                 logger.warning(f"Gemini blocked: {response.prompt_feedback.block_reason}")
                 return f"[Summary blocked: {response.prompt_feedback.block_reason}]"
            else: logger.warning("Gemini summary empty."); return "[Error: No summary generated]"
        except Exception as e: return self._handle_api_error(e, "summarization")