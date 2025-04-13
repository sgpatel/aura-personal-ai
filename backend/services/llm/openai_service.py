# backend/services/llm/openai_service.py
import logging
from typing import List, Dict, Any
from openai import OpenAI, APIError, RateLimitError # Use OpenAI v1.x+ library

from .base import LLMService
from backend.core.config import settings # To potentially access model specifics later

logger = logging.getLogger(__name__)

class OpenAILLMService(LLMService):
    provider = "openai"

    def __init__(self, api_key: str):
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully.")
            # Optional: Test connection with a simple request like listing models
            # self.client.models.list()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            # Depending on desired behavior, could raise error or handle gracefully
            self.client = None # Indicate failure

    def _handle_api_error(self, error: APIError, context: str) -> str:
        logger.error(f"OpenAI API Error ({context}): Status={error.status_code} Message={error.message}", exc_info=True)
        # You might want different error messages based on status code
        if isinstance(error, RateLimitError):
            return f"[Error: OpenAI rate limit exceeded. Please try again later.]"
        return f"[Error: OpenAI API request failed. {error.message}]"

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 150, **kwargs) -> str:
        """Generates simple text completion using OpenAI."""
        if not self.client: return "[Error: OpenAI client not initialized]"
        logger.info(f"Generating text with OpenAI model: {model}")
        try:
            # Use chat completion endpoint for newer models like GPT-3.5 Turbo and GPT-4
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7, # Adjust creativity
                **kwargs # Pass additional parameters if needed
            )
            # Access the response content correctly
            if response.choices and response.choices[0].message:
                 return response.choices[0].message.content.strip()
            else:
                 logger.warning("OpenAI response structure unexpected or empty.")
                 return "[Error: Could not extract response from OpenAI]"

        except APIError as e:
            return self._handle_api_error(e, "text generation")
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI text generation: {e}", exc_info=True)
            return "[Error: An unexpected error occurred during text generation]"

    def generate_summary(self, documents: List[str], model: str = "gpt-4o", max_tokens: int = 300, **kwargs) -> str:
        """Generates a summary from documents using OpenAI."""
        if not self.client: return "[Error: OpenAI client not initialized]"
        if not documents: return "No documents provided for summarization."

        # Basic prompt engineering - combine documents
        # Consider token limits - might need chunking for very long docs
        full_text = "\n\n---\n\n".join(documents)
        prompt = f"Please summarize the key points from the following document(s):\n\n{full_text}\n\nSummary:"

        logger.info(f"Generating summary with OpenAI model: {model}")
        try:
            response = self.client.chat.completions.create(
                model=model, # Use GPT-4o for potentially better summaries
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.5, # Lower temperature for more focused summary
                **kwargs
            )
            if response.choices and response.choices[0].message:
                 return response.choices[0].message.content.strip()
            else:
                 logger.warning("OpenAI summary response structure unexpected or empty.")
                 return "[Error: Could not extract summary from OpenAI]"

        except APIError as e:
            return self._handle_api_error(e, "summarization")
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI summarization: {e}", exc_info=True)
            return "[Error: An unexpected error occurred during summarization]"