"""
Settings configuration using pydantic-settings.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    app_name: str = "Music Text Generator"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Directories
    uploads_dir: Path = Field(default_factory=lambda: Path("uploads"))
    outputs_dir: Path = Field(default_factory=lambda: Path("outputs"))
    
    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Model settings
    default_whisper_model: str = "medium"
    default_ollama_model: str = "llama3"
    
    # Job settings
    max_file_size_mb: int = 100
    job_cleanup_days: int = 7
    
    # OpenAI settings
    openai_api_key: str | None = None
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    
    class Config:
        env_prefix = "MTG_"
        case_sensitive = False


# Global settings instance
settings = Settings()
