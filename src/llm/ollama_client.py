import json
import uuid
import httpx
from src.llm.base import LLMClient


class OllamaClient(LLMClient):
    """
    Client Ollama avec support tool_use via prompt engineering.
    Ollama ne supporte pas nativement le format tool_use d'Anthropic,
    donc on guide le modèle via le prompt pour produire du JSON structuré.
    """

    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self._host = host.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return f"ollama/{self._model}"

    def chat_with_tools(self, system, messages, tools, max_tokens=8192):
        tools_desc = self._format_tools(tools)
        enhanced_system = f"""{system}

--- INSTRUCTION DE FORMAT ---
Tu DOIS répondre UNIQUEMENT avec un objet JSON valide de ce format exact :
{{
  "tool_calls": [
    {{
      "name": "<nom_outil>",
      "input": {{ <paramètres selon le schéma> }}
    }}
  ]
}}

Outils disponibles :
{tools_desc}

Ne réponds JAMAIS avec du texte libre. JSON uniquement."""

        ollama_messages = [{"role": "system", "content": enhanced_system}]
        for msg in messages:
            if isinstance(msg.get("content"), str):
                ollama_messages.append({"role": msg["role"], "content": msg["content"]})
            elif isinstance(msg.get("content"), list):
                text_parts = [
                    b.get("text", "") for b in msg["content"]
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                ollama_messages.append({
                    "role": msg["role"],
                    "content": " ".join(text_parts),
                })

        resp = httpx.post(
            f"{self._host}/api/chat",
            json={
                "model": self._model,
                "messages": ollama_messages,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.1},
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()

        tool_calls = self._parse_tool_calls(raw)
        stop_reason = "tool_use" if tool_calls else "end_turn"
        return stop_reason, tool_calls, []

    def _format_tools(self, tools: list[dict]) -> str:
        lines = []
        for t in tools:
            props = t.get("input_schema", {}).get("properties", {})
            required = t.get("input_schema", {}).get("required", [])
            lines.append(f"• {t['name']}: {t.get('description', '')}")
            for p, schema in props.items():
                req = " [REQUIS]" if p in required else ""
                lines.append(f"  - {p}{req}: {schema.get('description', '')}")
        return "\n".join(lines)

    def _parse_tool_calls(self, raw: str) -> list[dict]:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1:
                return []
            data = json.loads(raw[start:end])
            calls = data.get("tool_calls", [])
            return [
                {"id": str(uuid.uuid4()), "name": c["name"], "input": c["input"]}
                for c in calls if "name" in c and "input" in c
            ]
        except (json.JSONDecodeError, KeyError):
            return []
