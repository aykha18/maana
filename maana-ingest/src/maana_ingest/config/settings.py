"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL",
    )
    whisper_model: str = Field(default="large-v3", alias="WHISPER_MODEL")
    segment_length: int = Field(default=600, alias="SEGMENT_LENGTH")
    download_retries: int = Field(default=3, alias="DOWNLOAD_RETRIES")
    output_dir: Path = Field(default=Path("./output"), alias="OUTPUT_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


def get_settings() -> Settings:
    """Return a fresh settings object."""

    return Settings()
