"""Application configuration using environment variables."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Hindsight
    hindsight_base_url: str = "https://api.hindsight.vectorize.io"
    hindsight_api_key: str = ""
    hindsight_bank_id: str = "incident-response-team"

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"

    # Database
    database_url: str = "sqlite:///./incident_response.db"

    # Frontend
    frontend_api_url: str = "http://localhost:8000"

    # App
    app_name: str = "Incident Response Agent"
    debug: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
