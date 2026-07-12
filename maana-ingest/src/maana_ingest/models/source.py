"""Source intake and download models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class SourceType(StrEnum):
    """Supported source types."""

    YOUTUBE = "youtube"


class SourceRequest(BaseModel):
    """Validated input for source ingestion."""

    url: str
    source_type: SourceType = SourceType.YOUTUBE
    output_dir: Path

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be a valid http or https URL")
        return value

    @field_validator("output_dir", mode="before")
    @classmethod
    def normalize_output_dir(cls, value: str | Path) -> Path:
        return Path(value).expanduser()


class SourceMetadata(BaseModel):
    """Normalized source metadata persisted for a lecture."""

    title: str
    speaker: str
    duration: int | None = None
    upload_date: str | None = None
    youtube_id: str
    description: str | None = None
    thumbnail: str | None = None
    channel: str | None = None
    original_url: str

    @classmethod
    def from_yt_dlp_info(cls, info: dict[str, object], original_url: str) -> "SourceMetadata":
        title = str(info.get("title") or "untitled-lecture")
        channel = _clean_optional_text(info.get("channel") or info.get("uploader"))
        speaker = _clean_optional_text(
            info.get("creator")
            or info.get("artist")
            or info.get("uploader")
            or info.get("channel")
        ) or "unknown-speaker"
        youtube_id = str(info.get("id") or "unknown-id")
        duration = _coerce_int(info.get("duration"))
        upload_date = _clean_optional_text(info.get("upload_date"))
        description = _clean_optional_text(info.get("description"))
        thumbnail = _clean_optional_text(info.get("thumbnail"))

        return cls(
            title=title,
            speaker=speaker,
            duration=duration,
            upload_date=upload_date,
            youtube_id=youtube_id,
            description=description,
            thumbnail=thumbnail,
            channel=channel,
            original_url=original_url,
        )


class DownloadResult(BaseModel):
    """Persisted outputs from the download stage."""

    request: SourceRequest
    lecture_root: Path
    source_dir: Path
    metadata_path: Path
    raw_info_path: Path
    source_request_path: Path
    raw_media_path: Path | None = None
    skipped: bool = False
    downloaded_files: list[Path] = Field(default_factory=list)


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
