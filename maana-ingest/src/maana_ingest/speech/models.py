"""Speech recognition stage models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class SegmentTranscript(BaseModel):
    """Single ASR segment persisted to disk."""

    id: int
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    confidence: float | None = None
    no_speech_prob: float | None = None


class ChapterTranscript(BaseModel):
    """Transcription outputs for a single chapter."""

    chapter_number: int
    source_audio_path: Path
    raw_json_path: Path
    text_path: Path
    srt_path: Path
    vtt_path: Path
    language: str | None = None
    language_probability: float | None = None
    duration: float | None = None
    text: str = ""
    segment_count: int = 0
    skipped: bool = False
    segments: list[SegmentTranscript] = Field(default_factory=list)


class TranscriptionManifest(BaseModel):
    """Manifest of all chapter-level transcription outputs."""

    lecture_root: Path
    transcripts_dir: Path
    model_name: str
    device: str
    compute_type: str
    beam_size: int
    requested_language: str | None = None
    completed_chapters: int = 0
    skipped_chapters: int = 0
    chapter_transcripts: list[ChapterTranscript] = Field(default_factory=list)


class TranscriptionResult(BaseModel):
    """Phase 3 result surfaced to the CLI."""

    lecture_root: Path
    transcription_manifest_path: Path
    model_name: str
    device: str
    compute_type: str
    completed_chapters: int
    skipped_chapters: int
    chapter_transcripts: list[ChapterTranscript] = Field(default_factory=list)
