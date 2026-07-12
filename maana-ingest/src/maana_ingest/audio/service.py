"""Audio normalization and segmentation workflow."""

from __future__ import annotations

import contextlib
import json
import math
import shutil
import subprocess
import wave
from collections.abc import Callable
from pathlib import Path

from maana_ingest.audio.models import AudioPreparationResult, Chapter, ChapterManifest
from maana_ingest.config import Settings
from maana_ingest.download import LectureWorkspace


class AudioPreparationError(RuntimeError):
    """Raised when audio normalization or segmentation fails."""


class AudioPreparationService:
    """Prepare lecture audio for transcription."""

    def __init__(
        self,
        settings: Settings,
        *,
        ffmpeg_runner: Callable[[list[str]], None] | None = None,
    ) -> None:
        self._settings = settings
        self._ffmpeg_runner = ffmpeg_runner or self._run_ffmpeg

    def prepare_audio(
        self,
        lecture_path: Path,
        *,
        trim_silence: bool | None = None,
        segment_length: int | None = None,
    ) -> AudioPreparationResult:
        workspace = self._resolve_workspace(lecture_path)
        workspace.ensure_exists()
        source_media_path = workspace.find_raw_media_path()
        if source_media_path is None:
            raise AudioPreparationError(
                f"No source media file found in lecture workspace: {workspace.source_dir}"
            )

        self.ensure_ffmpeg_available()
        effective_trim_silence = self._settings.trim_silence if trim_silence is None else trim_silence
        effective_segment_length = segment_length or self._settings.segment_length
        if effective_segment_length <= 0:
            raise AudioPreparationError("segment length must be greater than zero")

        self.normalize_audio(source_media_path, workspace.normalized_audio_path, trim_silence=effective_trim_silence)
        manifest = self.split_normalized_audio(
            workspace.normalized_audio_path,
            workspace.chapters_dir,
            segment_length=effective_segment_length,
            source_media_path=source_media_path,
        )
        self._write_manifest(workspace.chapter_manifest_path, manifest)

        return AudioPreparationResult(
            lecture_root=workspace.lecture_root,
            source_media_path=source_media_path,
            normalized_audio_path=workspace.normalized_audio_path,
            chapter_manifest_path=workspace.chapter_manifest_path,
            chapters=manifest.chapters,
            ffmpeg_binary=self._settings.ffmpeg_binary,
        )

    def ensure_ffmpeg_available(self) -> None:
        ffmpeg_path = shutil.which(self._settings.ffmpeg_binary)
        if ffmpeg_path is None:
            raise AudioPreparationError(
                f"FFmpeg binary not found on PATH: {self._settings.ffmpeg_binary}"
            )
        try:
            self._ffmpeg_runner([self._settings.ffmpeg_binary, "-version"])
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AudioPreparationError(
                f"FFmpeg preflight failed for binary: {self._settings.ffmpeg_binary}"
            ) from exc

    def normalize_audio(
        self,
        source_media_path: Path,
        normalized_audio_path: Path,
        *,
        trim_silence: bool,
    ) -> None:
        normalized_audio_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self._settings.ffmpeg_binary,
            "-y",
            "-i",
            str(source_media_path),
            "-vn",
            "-ac",
            str(self._settings.audio_channels),
            "-ar",
            str(self._settings.audio_sample_rate),
            "-c:a",
            "pcm_s16le",
        ]
        if trim_silence:
            command.extend(
                [
                    "-af",
                    "silenceremove=start_periods=1:start_silence=0.3:start_threshold=-35dB:"
                    "stop_periods=1:stop_silence=0.5:stop_threshold=-35dB",
                ]
            )
        command.append(str(normalized_audio_path))
        try:
            self._ffmpeg_runner(command)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AudioPreparationError(f"FFmpeg normalization failed for: {source_media_path}") from exc

    def split_normalized_audio(
        self,
        normalized_audio_path: Path,
        chapters_dir: Path,
        *,
        segment_length: int,
        source_media_path: Path,
    ) -> ChapterManifest:
        chapters_dir.mkdir(parents=True, exist_ok=True)
        self._clear_existing_chapters(chapters_dir)

        with contextlib.closing(wave.open(str(normalized_audio_path), "rb")) as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            total_duration = frame_count / frame_rate if frame_rate else 0.0
            frames_per_segment = frame_rate * segment_length
            chapter_count = max(1, math.ceil(frame_count / frames_per_segment)) if frame_rate else 1
            chapters: list[Chapter] = []

            for index in range(chapter_count):
                chunk_frames = wav_file.readframes(frames_per_segment)
                chapter_file = chapters_dir / f"chapter-{index + 1:03d}.wav"
                with contextlib.closing(wave.open(str(chapter_file), "wb")) as chapter_wav:
                    chapter_wav.setnchannels(channels)
                    chapter_wav.setsampwidth(sample_width)
                    chapter_wav.setframerate(frame_rate)
                    chapter_wav.writeframes(chunk_frames)

                start = float(index * segment_length)
                end = min(total_duration, float((index + 1) * segment_length))
                chapters.append(
                    Chapter(
                        chapter_number=index + 1,
                        start=round(start, 3),
                        end=round(end, 3),
                        duration=round(max(0.0, end - start), 3),
                        file=chapter_file.resolve(),
                    )
                )

        return ChapterManifest(
            source_media_path=source_media_path.resolve(),
            normalized_audio_path=normalized_audio_path.resolve(),
            segment_length=segment_length,
            total_duration=round(total_duration, 3),
            chapters=chapters,
        )

    @staticmethod
    def _resolve_workspace(lecture_path: Path) -> LectureWorkspace:
        path = lecture_path.expanduser().resolve()
        if path.is_dir():
            if (path / "source").exists() and (path / "metadata").exists():
                return LectureWorkspace.from_lecture_root(path)
            raise AudioPreparationError(f"Directory does not look like a lecture workspace: {path}")

        if path.is_file():
            if path.parent.name == "source":
                return LectureWorkspace.from_lecture_root(path.parent.parent)
            raise AudioPreparationError(
                "File input must point to a source media file inside a lecture workspace source directory"
            )

        raise AudioPreparationError(f"Lecture path does not exist: {path}")

    @staticmethod
    def _clear_existing_chapters(chapters_dir: Path) -> None:
        for path in chapters_dir.glob("chapter-*.wav"):
            path.unlink()

    @staticmethod
    def _write_manifest(path: Path, manifest: ChapterManifest) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")

    @staticmethod
    def _run_ffmpeg(command: list[str]) -> None:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
