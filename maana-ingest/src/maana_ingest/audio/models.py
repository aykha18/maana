"""Audio stage models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Single audio chapter descriptor."""

    chapter_number: int
    start: float
    end: float
    duration: float
    file: Path


class ChapterManifest(BaseModel):
    """Manifest for normalized audio and chapter files."""

    source_media_path: Path
    normalized_audio_path: Path
    segment_length: int
    total_duration: float
    chapters: list[Chapter] = Field(default_factory=list)


class AudioPreparationResult(BaseModel):
    """Outputs produced by Phase 2 audio preparation."""

    lecture_root: Path
    source_media_path: Path
    normalized_audio_path: Path
    chapter_manifest_path: Path
    chapters: list[Chapter] = Field(default_factory=list)
    ffmpeg_binary: str
