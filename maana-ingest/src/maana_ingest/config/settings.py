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
    ffmpeg_binary: str = Field(default="ffmpeg", alias="FFMPEG_BINARY")
    audio_sample_rate: int = Field(default=16000, alias="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, alias="AUDIO_CHANNELS")
    trim_silence: bool = Field(default=False, alias="TRIM_SILENCE")
    whisper_language: str | None = Field(default=None, alias="WHISPER_LANGUAGE")
    whisper_beam_size: int = Field(default=5, alias="WHISPER_BEAM_SIZE")
    whisper_compute_type: str | None = Field(default=None, alias="WHISPER_COMPUTE_TYPE")
    clean_merge_gap_seconds: float = Field(default=1.5, alias="CLEAN_MERGE_GAP_SECONDS")
    annotation_provider: str = Field(default="mock", alias="ANNOTATION_PROVIDER")
    annotation_model: str = Field(default="mock-annotation-model", alias="ANNOTATION_MODEL")
    annotation_base_url: str | None = Field(default=None, alias="ANNOTATION_BASE_URL")
    annotation_api_key: str = Field(default="", alias="ANNOTATION_API_KEY")
    annotation_timeout_seconds: float = Field(default=60.0, alias="ANNOTATION_TIMEOUT_SECONDS")
    annotation_prompt_version: str = Field(default="v1", alias="ANNOTATION_PROMPT_VERSION")
    canonical_registry_path: Path | None = Field(default=None, alias="CANONICAL_REGISTRY_PATH")
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
