from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Interface commune pour tous les providers LLM."""

    @abstractmethod
    def chat_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 8192,
    ) -> tuple[str, list[dict], list[dict]]:
        """
        Retourne (stop_reason, tool_calls, content_blocks).
        tool_calls : liste de dicts {"id": str, "name": str, "input": dict}
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...
