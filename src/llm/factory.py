from src.llm.base import LLMClient


def get_llm_client() -> LLMClient:
    from config import settings

    if settings.LLM_PROVIDER == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY requis quand LLM_PROVIDER=anthropic")
        from src.llm.anthropic_client import AnthropicClient
        return AnthropicClient(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
        )

    from src.llm.ollama_client import OllamaClient
    return OllamaClient(host=settings.OLLAMA_HOST, model=settings.OLLAMA_MODEL)
