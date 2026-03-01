from app.config import settings
from app.core.llm.base import LLMProvider
from app.core.llm.groq_provider import GroqProvider
from app.core.llm.ollama_provider import OllamaProvider


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    return GroqProvider()
