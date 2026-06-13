from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path
from typing import Literal


class Settings(BaseSettings):

    # ── LLM ──────────────────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["ollama", "anthropic"] = "ollama"

    # Ollama (gratuit, local)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Anthropic (optionnel, payant)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-opus-4-8"

    # ── Email IMAP ────────────────────────────────────────────────────────────
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_SSL: bool = True
    IMAP_USERNAME: str = ""
    IMAP_PASSWORD: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587

    # ── Comportement agent ────────────────────────────────────────────────────
    MAX_EMAILS_PER_FETCH: int = 50
    REFRESH_INTERVAL_MINUTES: int = 30
    AGENT_LANGUAGE: str = "fr"

    # ── Base de données ───────────────────────────────────────────────────────
    STAFY_DB_PATH: str = "stafy.db"

    # ── Dashboard ─────────────────────────────────────────────────────────────
    DASHBOARD_HOST: str = "0.0.0.0"
    DASHBOARD_PORT: int = 8000
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD: str = "changeme"
    SECRET_KEY: str = "change-this-secret-key-in-production"

    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def check_anthropic_key(cls, v, values):
        return v

    @field_validator("IMAP_HOST")
    @classmethod
    def check_imap_host(cls, v):
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
