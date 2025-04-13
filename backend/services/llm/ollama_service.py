# backend/services/llm/ollama_service.py
import logging
from typing import List, Dict, Any
import httpx # Use httpx for async requests

from .base import LLMService
from backend.core.config import settings

logger = logging.getLogger(__name__)

class OllamaLLMService(LLMService):
    provider = "ollama"

    def __init__(self, base_url: str, default_model: str):
        # Ensure base_url doesn't end with a slash for easier joining
        self.base_url = base_url.rstrip('/')
        self.model = default_model
        # Use an async client for potential async routes later
        self.async_client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0) # Increase timeout
        logger.info(f"Ollama client configured for base URL: {self.base_url}, model: {self.model}")
        # TODO: Add a check to see if Ollama server is reachable on init?

    async def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """ Helper to make requests to Ollama API """
        try:
            response = await self.async_client.post(endpoint, json=payload)
            response.raise_for_status() # Raise exception for 4xx/5xx errors
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error to {e.request.url}: {e}", exc_info=True)
            raise ConnectionError(f"Could not connect to Ollama server at {self.base_url}. Is it running?") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}", exc_info=True)
            # Try to parse Ollama's error message if available
            error_detail = e.response.text
            try: error_detail = e.response.json().get("error", error_detail)
            except: pass
            raise ValueError(f"Ollama API request failed: {e.response.status_code} - {error_detail}") from e
        except Exception as e:
             logger.error(f"Unexpected error during Ollama request: {e}", exc_info=True)
             raise

    # NOTE: Ollama service methods need to be async if using httpx.AsyncClient
    async def generate_text(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generates simple text completion using Ollama."""
        selected_model = model or self.model
        logger.info(f"Generating text with Ollama model: {selected_model}")
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False, # Get full response at once
            "options": { # Optional parameters
                "temperature": 0.7,
                # "num_predict": 150 # Equivalent to max_tokens, adjust as needed
            }
        }
        try:
            response_data = await self._make_request("/api/generate", payload)
            return response_data.get("response", "").strip()
        except (ConnectionError, ValueError) as e:
            return f"[Error: Ollama request failed. {e}]"
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e}", exc_info=True)
            return "[Error: Unexpected Ollama error]"


    async def generate_summary(self, documents: List[str], model: str = None, **kwargs) -> str:
        """Generates a summary from documents using Ollama."""
        if not documents: return "No documents provided for summarization."

        selected_model = model or self.model
        full_text = "\n\n---\n\n".join(documents)
        # Simple summary prompt
        prompt = f"Please provide a concise summary of the following document(s):\n\n{full_text}\n\nSummary:"

        logger.info(f"Generating summary with Ollama model: {selected_model}")
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
             "options": {
                "temperature": 0.5,
                # "num_predict": 300 # Limit summary length
            }
        }
        try:
            response_data = await self._make_request("/api/generate", payload)
            return response_data.get("response", "").strip()
        except (ConnectionError, ValueError) as e:
             return f"[Error: Ollama summary request failed. {e}]"
        except Exception as e:
            logger.error(f"Unexpected Ollama summary error: {e}", exc_info=True)
            return "[Error: Unexpected Ollama summary error]"

    # Need to properly close the client if the app shuts down
    async def close_client(self):
        await self.async_client.aclose()
        logger.info("Ollama httpx client closed.")