"""Deterministic lecture workspace layout for downloaded sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from maana_ingest.models import SourceMetadata


@dataclass(frozen=True)
class LectureWorkspace:
    """Filesystem layout for a single lecture download."""

    lecture_root: Path
    source_dir: Path
    audio_dir: Path
    chapters_dir: Path
    transcripts_dir: Path
    transcript_chapters_dir: Path
    cleaned_dir: Path
    annotation_dir: Path
    annotation_chapters_dir: Path
    knowledge_dir: Path
    knowledge_chapters_dir: Path
    metadata_dir: Path
    logs_dir: Path
    metadata_path: Path
    raw_info_path: Path
    source_request_path: Path
    normalized_audio_path: Path
    chapter_manifest_path: Path
    transcription_manifest_path: Path
    cleaned_transcript_json_path: Path
    cleaned_transcript_markdown_path: Path
    annotation_manifest_path: Path
    knowledge_manifest_path: Path

    @classmethod
    def build(cls, base_output_dir: Path, metadata: SourceMetadata) -> "LectureWorkspace":
        base_dir = base_output_dir.expanduser().resolve()
        speaker_slug = _slugify(metadata.speaker or metadata.channel or "unknown-speaker")
        lecture_slug = _slugify(metadata.title or metadata.youtube_id)
        lecture_root = base_dir / "lectures" / speaker_slug / f"{metadata.youtube_id}-{lecture_slug}"
        metadata_dir = lecture_root / "metadata"

        return cls(
            lecture_root=lecture_root,
            source_dir=lecture_root / "source",
            audio_dir=lecture_root / "audio",
            chapters_dir=lecture_root / "audio" / "chapters",
            transcripts_dir=lecture_root / "transcripts",
            transcript_chapters_dir=lecture_root / "transcripts" / "chapters",
            cleaned_dir=lecture_root / "cleaned",
            annotation_dir=lecture_root / "annotations",
            annotation_chapters_dir=lecture_root / "annotations" / "chapters",
            knowledge_dir=lecture_root / "knowledge",
            knowledge_chapters_dir=lecture_root / "knowledge" / "chapters",
            metadata_dir=metadata_dir,
            logs_dir=lecture_root / "logs",
            metadata_path=metadata_dir / "metadata.json",
            raw_info_path=metadata_dir / "raw_info.json",
            source_request_path=metadata_dir / "source_request.json",
            normalized_audio_path=lecture_root / "audio" / "normalized.wav",
            chapter_manifest_path=lecture_root / "audio" / "chapters" / "manifest.json",
            transcription_manifest_path=lecture_root / "transcripts" / "manifest.json",
            cleaned_transcript_json_path=lecture_root / "cleaned" / "transcript.json",
            cleaned_transcript_markdown_path=lecture_root / "cleaned" / "clean_transcript.md",
            annotation_manifest_path=lecture_root / "annotations" / "manifest.json",
            knowledge_manifest_path=lecture_root / "knowledge" / "manifest.json",
        )

    @classmethod
    def from_lecture_root(cls, lecture_root: Path) -> "LectureWorkspace":
        root = lecture_root.expanduser().resolve()
        metadata_dir = root / "metadata"

        return cls(
            lecture_root=root,
            source_dir=root / "source",
            audio_dir=root / "audio",
            chapters_dir=root / "audio" / "chapters",
            transcripts_dir=root / "transcripts",
            transcript_chapters_dir=root / "transcripts" / "chapters",
            cleaned_dir=root / "cleaned",
            annotation_dir=root / "annotations",
            annotation_chapters_dir=root / "annotations" / "chapters",
            knowledge_dir=root / "knowledge",
            knowledge_chapters_dir=root / "knowledge" / "chapters",
            metadata_dir=metadata_dir,
            logs_dir=root / "logs",
            metadata_path=metadata_dir / "metadata.json",
            raw_info_path=metadata_dir / "raw_info.json",
            source_request_path=metadata_dir / "source_request.json",
            normalized_audio_path=root / "audio" / "normalized.wav",
            chapter_manifest_path=root / "audio" / "chapters" / "manifest.json",
            transcription_manifest_path=root / "transcripts" / "manifest.json",
            cleaned_transcript_json_path=root / "cleaned" / "transcript.json",
            cleaned_transcript_markdown_path=root / "cleaned" / "clean_transcript.md",
            annotation_manifest_path=root / "annotations" / "manifest.json",
            knowledge_manifest_path=root / "knowledge" / "manifest.json",
        )

    def ensure_exists(self) -> None:
        """Create all workspace directories."""

        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.chapters_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_chapters_dir.mkdir(parents=True, exist_ok=True)
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
        self.annotation_dir.mkdir(parents=True, exist_ok=True)
        self.annotation_chapters_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_chapters_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def find_raw_media_path(self) -> Path | None:
        """Return the downloaded source media file if present."""

        for candidate in sorted(self.source_dir.glob("source.*")):
            if _is_primary_media_file(candidate):
                return candidate
        return None

    def list_downloaded_files(self) -> list[Path]:
        """Return all files currently stored in the source directory."""

        return sorted(path for path in self.source_dir.iterdir() if path.is_file())


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "unknown"


def _is_primary_media_file(path: Path) -> bool:
    if not path.is_file():
        return False

    sidecar_suffixes = {
        ".description",
        ".jpg",
        ".jpeg",
        ".json",
        ".png",
        ".srt",
        ".ttml",
        ".txt",
        ".vtt",
        ".webp",
    }
    if path.suffix.lower() in sidecar_suffixes:
        return False

    return path.name.count(".") == 1
