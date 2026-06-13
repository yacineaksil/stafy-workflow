from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    GMAIL_CREDENTIALS_FILE: str = "credentials.json"
    GMAIL_TOKEN_FILE: str = "token.json"
    MAX_EMAILS_PER_FETCH: int = 50
    DASHBOARD_HOST: str = "0.0.0.0"
    DASHBOARD_PORT: int = 8000
    AGENT_LANGUAGE: str = "fr"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
