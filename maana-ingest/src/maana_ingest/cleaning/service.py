"""Deterministic transcript cleaning on top of raw ASR outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from maana_ingest.cleaning.models import (
    CleanedChapterTranscript,
    CleanedTranscriptDocument,
    CleanedTranscriptSegment,
    CleaningResult,
)
from maana_ingest.config import Settings
from maana_ingest.download import LectureWorkspace
from maana_ingest.speech import ChapterTranscript, SegmentTranscript, TranscriptionManifest

ARABIC_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")
MULTISPACE_RE = re.compile(r"\s+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([،؛؟!.,:)\]\}»”])")
SPACE_AFTER_OPEN_RE = re.compile(r"([(\[\{«“])\s+")
TERMINAL_PUNCTUATION = ("۔", "؟", ".", "!", "?")


class TranscriptCleaningError(RuntimeError):
    """Raised when transcript cleaning cannot proceed."""


class TranscriptCleaningService:
    """Normalize and merge raw ASR segments into cleaned transcript outputs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def clean_transcripts(
        self,
        lecture_path: Path,
        *,
        force: bool = False,
    ) -> CleaningResult:
        workspace = self._resolve_workspace(lecture_path)
        workspace.ensure_exists()

        if (
            not force
            and workspace.cleaned_transcript_json_path.exists()
            and workspace.cleaned_transcript_markdown_path.exists()
        ):
            document = CleanedTranscriptDocument.model_validate_json(
                workspace.cleaned_transcript_json_path.read_text(encoding="utf-8")
            )
            return CleaningResult(
                lecture_root=document.lecture_root,
                cleaned_json_path=document.cleaned_json_path,
                cleaned_markdown_path=document.cleaned_markdown_path,
                total_chapters=document.total_chapters,
                total_segments=document.total_segments,
                merged_segment_count=document.merged_segment_count,
            )

        transcription_manifest = self._load_transcription_manifest(workspace.transcription_manifest_path)
        if not transcription_manifest.chapter_transcripts:
            raise TranscriptCleaningError("Transcription manifest contains no chapter transcripts")

        cleaned_chapters: list[CleanedChapterTranscript] = []
        merged_segment_count = 0
        total_segments = 0

        for chapter in transcription_manifest.chapter_transcripts:
            raw_payload = self._load_raw_transcript(chapter.raw_json_path)
            source_segments = [
                SegmentTranscript.model_validate(segment_payload)
                for segment_payload in raw_payload.get("segments", [])
            ]
            cleaned_segments = self._clean_segments(chapter.chapter_number, source_segments)
            merged_segment_count += max(0, len(source_segments) - len(cleaned_segments))
            total_segments += len(cleaned_segments)
            cleaned_chapters.append(
                CleanedChapterTranscript(
                    chapter_number=chapter.chapter_number,
                    language=raw_payload.get("language") or chapter.language,
                    source_audio_path=chapter.source_audio_path,
                    raw_transcript_path=chapter.raw_json_path,
                    cleaned_text="\n".join(segment.cleaned_text for segment in cleaned_segments if segment.cleaned_text),
                    original_text="\n".join(
                        segment.original_text for segment in cleaned_segments if segment.original_text
                    ),
                    segments=cleaned_segments,
                )
            )

        document = CleanedTranscriptDocument(
            lecture_root=workspace.lecture_root.resolve(),
            transcription_manifest_path=workspace.transcription_manifest_path.resolve(),
            cleaned_json_path=workspace.cleaned_transcript_json_path.resolve(),
            cleaned_markdown_path=workspace.cleaned_transcript_markdown_path.resolve(),
            total_chapters=len(cleaned_chapters),
            total_segments=total_segments,
            merged_segment_count=merged_segment_count,
            chapters=cleaned_chapters,
        )
        self._write_json(workspace.cleaned_transcript_json_path, document.model_dump(mode="json"))
        workspace.cleaned_transcript_markdown_path.write_text(
            self._render_markdown(document),
            encoding="utf-8",
        )

        return CleaningResult(
            lecture_root=document.lecture_root,
            cleaned_json_path=document.cleaned_json_path,
            cleaned_markdown_path=document.cleaned_markdown_path,
            total_chapters=document.total_chapters,
            total_segments=document.total_segments,
            merged_segment_count=document.merged_segment_count,
        )

    def _clean_segments(
        self,
        chapter_number: int,
        source_segments: list[SegmentTranscript],
    ) -> list[CleanedTranscriptSegment]:
        cleaned_segments: list[CleanedTranscriptSegment] = []
        merge_gap = self._settings.clean_merge_gap_seconds

        for source_segment in source_segments:
            normalized_text = normalize_transcript_text(source_segment.text)
            if not normalized_text:
                continue

            current = CleanedTranscriptSegment(
                chapter_number=chapter_number,
                start=source_segment.start,
                end=source_segment.end,
                original_text=source_segment.text.strip(),
                cleaned_text=normalized_text,
                original_segment_ids=[source_segment.id],
            )
            if cleaned_segments and _should_merge(cleaned_segments[-1], current, merge_gap):
                previous = cleaned_segments[-1]
                previous.original_text = f"{previous.original_text} {current.original_text}".strip()
                previous.cleaned_text = normalize_transcript_text(
                    f"{previous.cleaned_text} {current.cleaned_text}"
                )
                previous.end = current.end
                previous.original_segment_ids.extend(current.original_segment_ids)
                continue

            cleaned_segments.append(current)

        return cleaned_segments

    @staticmethod
    def _resolve_workspace(lecture_path: Path) -> LectureWorkspace:
        path = lecture_path.expanduser().resolve()
        if path.is_dir():
            if (path / "transcripts" / "manifest.json").exists():
                return LectureWorkspace.from_lecture_root(path)
            raise TranscriptCleaningError(
                f"Directory does not look like a transcribed lecture workspace: {path}"
            )

        if path.is_file():
            if path.name == "manifest.json" and path.parent.name == "transcripts":
                return LectureWorkspace.from_lecture_root(path.parent.parent)
            raise TranscriptCleaningError(
                "File input must point to a lecture transcription manifest inside the transcripts directory"
            )

        raise TranscriptCleaningError(f"Lecture path does not exist: {path}")

    @staticmethod
    def _load_transcription_manifest(path: Path) -> TranscriptionManifest:
        if not path.exists():
            raise TranscriptCleaningError(f"Transcription manifest not found: {path}")
        return TranscriptionManifest.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_raw_transcript(path: Path) -> dict[str, object]:
        if not path.exists():
            raise TranscriptCleaningError(f"Raw transcript JSON not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _render_markdown(document: CleanedTranscriptDocument) -> str:
        lines = [
            "# Clean Transcript",
            "",
            f"Total Chapters: {document.total_chapters}",
            f"Total Segments: {document.total_segments}",
            f"Merged Segments: {document.merged_segment_count}",
            "",
        ]
        for chapter in document.chapters:
            lines.append(f"## Chapter {chapter.chapter_number}")
            lines.append("")
            for segment in chapter.segments:
                lines.append(
                    f"- [{_format_timestamp(segment.start)} - {_format_timestamp(segment.end)}] "
                    f"{segment.cleaned_text}"
                )
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def normalize_transcript_text(text: str) -> str:
    """Normalize spacing and Urdu/Persian/Arabic punctuation deterministically."""

    normalized = MULTISPACE_RE.sub(" ", text.replace("\n", " ")).strip()
    if not normalized:
        return ""

    if ARABIC_SCRIPT_RE.search(normalized):
        normalized = normalized.replace(",", "،").replace(";", "؛").replace("?", "؟")
        normalized = _replace_terminal_period(normalized)

    normalized = SPACE_BEFORE_PUNCT_RE.sub(r"\1", normalized)
    normalized = SPACE_AFTER_OPEN_RE.sub(r"\1", normalized)
    normalized = normalized.replace(" ۔", "۔").replace(" ؟", "؟").replace(" ،", "،").replace(" ؛", "؛")
    normalized = normalized.replace("“ ", "“").replace(" ”", "”")
    return normalized.strip()


def _replace_terminal_period(text: str) -> str:
    if text.endswith("."):
        return text[:-1] + "۔"
    return text


def _should_merge(
    previous: CleanedTranscriptSegment,
    current: CleanedTranscriptSegment,
    merge_gap_seconds: float,
) -> bool:
    if not previous.cleaned_text or not current.cleaned_text:
        return False
    if previous.cleaned_text.endswith(TERMINAL_PUNCTUATION):
        return False
    if current.start - previous.end > merge_gap_seconds:
        return False
    return True


def _format_timestamp(value: float) -> str:
    total_milliseconds = int(round(value * 1000))
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
