# backend/services/llm/__init__.py
from backend.core.config import settings, logger
from .base import LLMService
from .openai_service import OpenAILLMService
from .gemini_service import GeminiLLMService
from .ollama_service import OllamaLLMService

# --- LLM Service Factory ---

# Cache the instance to avoid re-initialization on every call
_llm_service_instance = None

def get_llm_service(provider: str = None) -> LLMService:
    """
    Factory function to get the configured LLM service instance.
    Uses the DEFAULT_LLM_PROVIDER from settings if provider is not specified.
    """
    global _llm_service_instance
    # TODO: Add more robust caching or dependency injection if needed

    selected_provider = provider or settings.DEFAULT_LLM_PROVIDER

    # If instance exists and provider hasn't changed, return cached instance
    # Note: This simple cache doesn't handle config changes after startup well.
    if _llm_service_instance and _llm_service_instance.provider == selected_provider:
        return _llm_service_instance

    logger.info(f"Initializing LLM service for provider: {selected_provider}")

    if selected_provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured in settings.")
        _llm_service_instance = OpenAILLMService(api_key=settings.OPENAI_API_KEY)
    elif selected_provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Google API key is not configured in settings.")
        _llm_service_instance = GeminiLLMService(api_key=settings.GOOGLE_API_KEY)
    elif selected_provider == "ollama":
        if not settings.OLLAMA_BASE_URL:
             raise ValueError("Ollama Base URL is not configured in settings.")
        _llm_service_instance = OllamaLLMService(
            base_url=str(settings.OLLAMA_BASE_URL), # Ensure str
            default_model=settings.OLLAMA_DEFAULT_MODEL
        )
    else:
        raise ValueError(f"Unsupported LLM provider configured: {selected_provider}")

    _llm_service_instance.provider = selected_provider # Store provider in instance for caching check
    return _llm_service_instance