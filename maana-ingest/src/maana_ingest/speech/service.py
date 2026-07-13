"""faster-whisper speech recognition workflow."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Protocol

from faster_whisper import WhisperModel

from maana_ingest.audio import Chapter, ChapterManifest
from maana_ingest.config import Settings
from maana_ingest.download import LectureWorkspace
from maana_ingest.speech.models import (
    ChapterTranscript,
    SegmentTranscript,
    TranscriptionManifest,
    TranscriptionResult,
)


class SpeechRecognitionError(RuntimeError):
    """Raised when speech recognition cannot proceed."""


class WhisperModellike(Protocol):
    """Protocol for testable whisper model interactions."""

    def transcribe(
        self,
        audio: str,
        *,
        beam_size: int,
        language: str | None,
        vad_filter: bool,
    ) -> tuple[Iterable[Any], Any]: ...


ModelFactory = Callable[[str, str, str], WhisperModellike]
ProgressCallback = Callable[[str], None]


class SpeechRecognitionService:
    """Transcribe chapter audio into persistent outputs."""

    def __init__(
        self,
        settings: Settings,
        *,
        model_factory: ModelFactory | None = None,
    ) -> None:
        self._settings = settings
        self._model_factory = model_factory or self._create_model

    def transcribe_lecture(
        self,
        lecture_path: Path,
        *,
        language: str | None = None,
        force: bool = False,
        progress_callback: ProgressCallback | None = None,
    ) -> TranscriptionResult:
        workspace, selected_chapter_path = self._resolve_workspace(lecture_path)
        workspace.ensure_exists()
        chapter_manifest = self._load_chapter_manifest(workspace.chapter_manifest_path)
        chapters_to_process = self._select_chapters(chapter_manifest, selected_chapter_path)
        if not chapters_to_process:
            raise SpeechRecognitionError("Chapter manifest contains no chapter files to transcribe")

        device = self._detect_device()
        compute_type = self._settings.whisper_compute_type or (
            "float16" if device == "cuda" else "int8"
        )
        requested_language = language or self._settings.whisper_language
        beam_size = self._settings.whisper_beam_size
        model = self._model_factory(self._settings.whisper_model, device, compute_type)

        chapter_outputs: list[ChapterTranscript] = []
        completed = 0
        skipped = 0

        for chapter in chapters_to_process:
            chapter_output_dir = workspace.transcript_chapters_dir / f"chapter-{chapter.chapter_number:03d}"
            chapter_output_dir.mkdir(parents=True, exist_ok=True)
            raw_json_path = chapter_output_dir / "transcript.json"
            text_path = chapter_output_dir / "transcript.txt"
            srt_path = chapter_output_dir / "transcript.srt"
            vtt_path = chapter_output_dir / "transcript.vtt"

            if not force and self._outputs_exist(raw_json_path, text_path, srt_path, vtt_path):
                chapter_outputs.append(
                    self._load_existing_transcript(
                        chapter.chapter_number,
                        chapter.file,
                        raw_json_path,
                        text_path,
                        srt_path,
                        vtt_path,
                    )
                )
                skipped += 1
                if progress_callback is not None:
                    progress_callback(f"Skipped chapter {chapter.chapter_number}: existing outputs found")
                continue

            if progress_callback is not None:
                progress_callback(
                    f"Transcribing chapter {chapter.chapter_number}/{len(chapters_to_process)}"
                )

            chapter_transcript = self._transcribe_chapter(
                model=model,
                chapter_number=chapter.chapter_number,
                chapter_path=chapter.file,
                raw_json_path=raw_json_path,
                text_path=text_path,
                srt_path=srt_path,
                vtt_path=vtt_path,
                language=requested_language,
                beam_size=beam_size,
            )
            chapter_outputs.append(chapter_transcript)
            completed += 1

        manifest = TranscriptionManifest(
            lecture_root=workspace.lecture_root.resolve(),
            transcripts_dir=workspace.transcripts_dir.resolve(),
            model_name=self._settings.whisper_model,
            device=device,
            compute_type=compute_type,
            beam_size=beam_size,
            requested_language=requested_language,
            completed_chapters=completed,
            skipped_chapters=skipped,
            chapter_transcripts=chapter_outputs,
        )
        self._write_json(
            workspace.transcription_manifest_path,
            manifest.model_dump(mode="json"),
        )

        return TranscriptionResult(
            lecture_root=workspace.lecture_root.resolve(),
            transcription_manifest_path=workspace.transcription_manifest_path.resolve(),
            model_name=self._settings.whisper_model,
            device=device,
            compute_type=compute_type,
            completed_chapters=completed,
            skipped_chapters=skipped,
            chapter_transcripts=chapter_outputs,
        )

    def _transcribe_chapter(
        self,
        *,
        model: WhisperModellike,
        chapter_number: int,
        chapter_path: Path,
        raw_json_path: Path,
        text_path: Path,
        srt_path: Path,
        vtt_path: Path,
        language: str | None,
        beam_size: int,
    ) -> ChapterTranscript:
        try:
            segments_iterable, info = model.transcribe(
                str(chapter_path),
                beam_size=beam_size,
                language=language,
                vad_filter=True,
            )
        except Exception as exc:  # pragma: no cover - library failures vary
            raise SpeechRecognitionError(f"Failed to transcribe chapter: {chapter_path}") from exc

        segments = [self._normalize_segment(segment) for segment in segments_iterable]
        full_text = "\n".join(segment.text for segment in segments if segment.text).strip()
        chapter_payload = {
            "chapter_number": chapter_number,
            "source_audio_path": str(chapter_path.resolve()),
            "language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
            "duration": getattr(info, "duration", None),
            "text": full_text,
            "segments": [segment.model_dump(mode="json") for segment in segments],
        }
        self._write_json(raw_json_path, chapter_payload)
        text_path.write_text(full_text + ("\n" if full_text else ""), encoding="utf-8")
        srt_path.write_text(self._render_srt(segments), encoding="utf-8")
        vtt_path.write_text(self._render_vtt(segments), encoding="utf-8")

        return ChapterTranscript(
            chapter_number=chapter_number,
            source_audio_path=chapter_path.resolve(),
            raw_json_path=raw_json_path.resolve(),
            text_path=text_path.resolve(),
            srt_path=srt_path.resolve(),
            vtt_path=vtt_path.resolve(),
            language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
            duration=getattr(info, "duration", None),
            text=full_text,
            segment_count=len(segments),
            skipped=False,
            segments=segments,
        )

    def _load_existing_transcript(
        self,
        chapter_number: int,
        chapter_path: Path,
        raw_json_path: Path,
        text_path: Path,
        srt_path: Path,
        vtt_path: Path,
    ) -> ChapterTranscript:
        payload = json.loads(raw_json_path.read_text(encoding="utf-8"))
        segments = [
            SegmentTranscript.model_validate(segment_payload)
            for segment_payload in payload.get("segments", [])
        ]
        return ChapterTranscript(
            chapter_number=chapter_number,
            source_audio_path=chapter_path.resolve(),
            raw_json_path=raw_json_path.resolve(),
            text_path=text_path.resolve(),
            srt_path=srt_path.resolve(),
            vtt_path=vtt_path.resolve(),
            language=payload.get("language"),
            language_probability=payload.get("language_probability"),
            duration=payload.get("duration"),
            text=payload.get("text", ""),
            segment_count=len(segments),
            skipped=True,
            segments=segments,
        )

    @staticmethod
    def _normalize_segment(segment: Any) -> SegmentTranscript:
        avg_logprob = getattr(segment, "avg_logprob", None)
        confidence = None
        if isinstance(avg_logprob, (float, int)):
            confidence = round(min(1.0, math.exp(float(avg_logprob))), 6)

        return SegmentTranscript(
            id=int(getattr(segment, "id")),
            start=round(float(getattr(segment, "start")), 3),
            end=round(float(getattr(segment, "end")), 3),
            text=str(getattr(segment, "text")).strip(),
            avg_logprob=None if avg_logprob is None else round(float(avg_logprob), 6),
            confidence=confidence,
            no_speech_prob=_optional_float(getattr(segment, "no_speech_prob", None)),
        )

    @staticmethod
    def _render_srt(segments: list[SegmentTranscript]) -> str:
        blocks: list[str] = []
        for index, segment in enumerate(segments, start=1):
            blocks.append(
                f"{index}\n"
                f"{_format_timestamp(segment.start, srt=True)} --> {_format_timestamp(segment.end, srt=True)}\n"
                f"{segment.text}\n"
            )
        return "\n".join(blocks).rstrip() + ("\n" if blocks else "")

    @staticmethod
    def _render_vtt(segments: list[SegmentTranscript]) -> str:
        lines = ["WEBVTT", ""]
        for segment in segments:
            lines.append(
                f"{_format_timestamp(segment.start, srt=False)} --> {_format_timestamp(segment.end, srt=False)}"
            )
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _resolve_workspace(lecture_path: Path) -> tuple[LectureWorkspace, Path | None]:
        path = lecture_path.expanduser().resolve()
        if path.is_dir():
            if (path / "audio" / "chapters" / "manifest.json").exists():
                return LectureWorkspace.from_lecture_root(path), None
            raise SpeechRecognitionError(f"Directory does not look like a prepared lecture workspace: {path}")

        if path.is_file():
            if path.parent.name == "chapters" and path.suffix.lower() == ".wav":
                return LectureWorkspace.from_lecture_root(path.parent.parent.parent), path
            raise SpeechRecognitionError(
                "File input must point to a chapter WAV inside a lecture workspace"
            )

        raise SpeechRecognitionError(f"Lecture path does not exist: {path}")

    @staticmethod
    def _load_chapter_manifest(path: Path) -> ChapterManifest:
        if not path.exists():
            raise SpeechRecognitionError(f"Chapter manifest not found: {path}")
        return ChapterManifest.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    @staticmethod
    def _create_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
        return WhisperModel(model_name, device=device, compute_type=compute_type)

    @staticmethod
    def _outputs_exist(*paths: Path) -> bool:
        return all(path.exists() for path in paths)

    @staticmethod
    def _select_chapters(
        chapter_manifest: ChapterManifest,
        selected_chapter_path: Path | None,
    ) -> list[Chapter]:
        if selected_chapter_path is None:
            return list(chapter_manifest.chapters)

        selected = [
            chapter
            for chapter in chapter_manifest.chapters
            if chapter.file.resolve() == selected_chapter_path.resolve()
        ]
        if not selected:
            raise SpeechRecognitionError(
                f"Selected chapter file is not present in the chapter manifest: {selected_chapter_path}"
            )
        return selected

    @staticmethod
    def _detect_device() -> str:
        try:
            import ctranslate2

            if ctranslate2.get_cuda_device_count() > 0:
                return "cuda"
        except Exception:
            pass
        return "cpu"


def _format_timestamp(value: float, *, srt: bool) -> str:
    total_milliseconds = int(round(value * 1000))
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    separator = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)
