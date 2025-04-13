# backend/services/llm/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMService(ABC):
    """Abstract Base Class for LLM Services."""

    provider: str = "base" # Identifier for the provider

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generates simple text completion."""
        pass

    @abstractmethod
    def generate_summary(self, documents: List[str], **kwargs) -> str:
        """Generates a summary from a list of documents."""
        pass

    # Add other common LLM tasks as needed (e.g., chat, classification)
    # @abstractmethod
    # def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
    #     """Handles chat-based interaction."""
    #     pass

