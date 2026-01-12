"""Application configuration"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App settings
    app_name: str = "AI Avatar System"
    app_version: str = "0.1.0"
    debug: bool = False

    # API Keys
    elevenlabs_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Storage paths
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    models_dir: Path = Path("./models")

    # Voice settings
    voice_sample_duration: int = 20  # seconds
    max_voice_file_size: int = 10 * 1024 * 1024  # 10MB

    # Avatar settings
    max_image_file_size: int = 5 * 1024 * 1024  # 5MB
    supported_image_formats: list = ["jpg", "jpeg", "png"]
    supported_audio_formats: list = ["mp3", "wav", "m4a", "ogg"]

    # LLM settings
    llm_model: str = "claude-3-sonnet-20240229"
    llm_max_tokens: int = 1024

    # Redis settings (for background tasks)
    redis_url: str = "redis://localhost:6379/0"

    # Database
    database_url: str = "sqlite+aiosqlite:///./avatar.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def init_directories():
    """Initialize required directories"""
    settings = get_settings()
    for dir_path in [settings.upload_dir, settings.output_dir, settings.models_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create subdirectories
        (dir_path / "voice").mkdir(exist_ok=True)
        (dir_path / "image").mkdir(exist_ok=True)
        (dir_path / "video").mkdir(exist_ok=True)
