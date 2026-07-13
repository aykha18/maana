"""Transcript cleaning stage models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class CleanedTranscriptSegment(BaseModel):
    """Timestamp-aware cleaned transcript segment."""

    chapter_number: int
    start: float
    end: float
    original_text: str
    cleaned_text: str
    original_segment_ids: list[int] = Field(default_factory=list)


class CleanedChapterTranscript(BaseModel):
    """Cleaned transcript for a single chapter."""

    chapter_number: int
    language: str | None = None
    source_audio_path: Path
    raw_transcript_path: Path
    cleaned_text: str = ""
    original_text: str = ""
    segments: list[CleanedTranscriptSegment] = Field(default_factory=list)


class CleanedTranscriptDocument(BaseModel):
    """Lecture-level cleaned transcript output."""

    lecture_root: Path
    transcription_manifest_path: Path
    cleaned_json_path: Path
    cleaned_markdown_path: Path
    total_chapters: int
    total_segments: int
    merged_segment_count: int
    chapters: list[CleanedChapterTranscript] = Field(default_factory=list)


class CleaningResult(BaseModel):
    """Phase 4 result surfaced to the CLI."""

    lecture_root: Path
    cleaned_json_path: Path
    cleaned_markdown_path: Path
    total_chapters: int
    total_segments: int
    merged_segment_count: int
