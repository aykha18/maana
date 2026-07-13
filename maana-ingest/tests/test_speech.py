from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.audio import Chapter, ChapterManifest
from maana_ingest.cli import app
from maana_ingest.download import LectureWorkspace
from maana_ingest.models import SourceMetadata
from maana_ingest.speech import SpeechRecognitionService, TranscriptionResult


class FakeSegment:
    def __init__(
        self,
        segment_id: int,
        start: float,
        end: float,
        text: str,
        *,
        avg_logprob: float = -0.2,
        no_speech_prob: float = 0.01,
    ) -> None:
        self.id = segment_id
        self.start = start
        self.end = end
        self.text = text
        self.avg_logprob = avg_logprob
        self.no_speech_prob = no_speech_prob


class FakeInfo:
    def __init__(
        self,
        *,
        language: str = "ur",
        language_probability: float = 0.97,
        duration: float = 42.0,
    ) -> None:
        self.language = language
        self.language_probability = language_probability
        self.duration = duration


class FakeWhisperModel:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def transcribe(
        self,
        audio: str,
        *,
        beam_size: int,
        language: str | None,
        vad_filter: bool,
    ) -> tuple[list[FakeSegment], FakeInfo]:
        self.calls.append(audio)
        chapter_name = Path(audio).stem
        return (
            [
                FakeSegment(0, 0.0, 1.2, f"{chapter_name} line one"),
                FakeSegment(1, 1.2, 2.5, f"{chapter_name} line two"),
            ],
            FakeInfo(),
        )


def test_transcription_service_persists_outputs_and_skips_existing(tmp_path: Path) -> None:
    workspace = _create_workspace_with_chapter_manifest(tmp_path)
    fake_model = FakeWhisperModel()
    settings = SimpleNamespace(
        whisper_model="tiny",
        whisper_compute_type=None,
        whisper_language=None,
        whisper_beam_size=3,
    )
    service = SpeechRecognitionService(
        settings=settings,
        model_factory=lambda model_name, device, compute_type: fake_model,
    )

    result = service.transcribe_lecture(workspace.lecture_root, language="ur")

    assert result.completed_chapters == 2
    assert result.skipped_chapters == 0
    assert len(fake_model.calls) == 2
    assert result.transcription_manifest_path.exists()

    chapter_dir = workspace.transcript_chapters_dir / "chapter-001"
    assert chapter_dir.joinpath("transcript.json").exists()
    assert chapter_dir.joinpath("transcript.txt").exists()
    assert chapter_dir.joinpath("transcript.srt").exists()
    assert chapter_dir.joinpath("transcript.vtt").exists()
    assert "WEBVTT" in chapter_dir.joinpath("transcript.vtt").read_text(encoding="utf-8")

    manifest = json.loads(result.transcription_manifest_path.read_text(encoding="utf-8"))
    assert manifest["model_name"] == "tiny"
    assert manifest["completed_chapters"] == 2
    assert manifest["requested_language"] == "ur"

    second = service.transcribe_lecture(workspace.lecture_root, language="ur")
    assert second.completed_chapters == 0
    assert second.skipped_chapters == 2
    assert len(fake_model.calls) == 2


def test_transcribe_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = TranscriptionResult(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        transcription_manifest_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "transcripts" / "manifest.json",
        model_name="tiny",
        device="cpu",
        compute_type="int8",
        completed_chapters=2,
        skipped_chapters=0,
        chapter_transcripts=[],
    )

    def fake_transcribe_lecture(
        self: object,
        lecture_path: Path,
        *,
        language: str | None = None,
        force: bool = False,
        progress_callback: object = None,
    ) -> TranscriptionResult:
        return expected

    monkeypatch.setattr(SpeechRecognitionService, "transcribe_lecture", fake_transcribe_lecture)

    result = runner.invoke(app, ["transcribe", str(tmp_path), "--language", "ur"])

    assert result.exit_code == 0
    assert "Transcription manifest:" in result.stdout
    assert "Completed chapters: 2" in result.stdout
    assert "Device: cpu" in result.stdout


def test_transcription_service_accepts_single_chapter_file(tmp_path: Path) -> None:
    workspace = _create_workspace_with_chapter_manifest(tmp_path)
    fake_model = FakeWhisperModel()
    settings = SimpleNamespace(
        whisper_model="tiny",
        whisper_compute_type=None,
        whisper_language=None,
        whisper_beam_size=3,
    )
    service = SpeechRecognitionService(
        settings=settings,
        model_factory=lambda model_name, device, compute_type: fake_model,
    )

    result = service.transcribe_lecture(workspace.chapters_dir / "chapter-002.wav", language="ur")

    assert result.completed_chapters == 1
    assert result.skipped_chapters == 0
    assert len(fake_model.calls) == 1
    assert fake_model.calls[0].endswith("chapter-002.wav")


def _create_workspace_with_chapter_manifest(base_dir: Path) -> LectureWorkspace:
    metadata = SourceMetadata(
        title="Dars-e-Ghalib",
        speaker="Ahmed Javed",
        duration=300,
        upload_date="20260712",
        youtube_id="demo123",
        description="Test lecture",
        thumbnail=None,
        channel="Danish Sara",
        original_url="https://youtu.be/demo123",
    )
    workspace = LectureWorkspace.build(base_dir, metadata)
    workspace.ensure_exists()

    chapter_one = workspace.chapters_dir / "chapter-001.wav"
    chapter_two = workspace.chapters_dir / "chapter-002.wav"
    chapter_one.write_bytes(b"RIFF")
    chapter_two.write_bytes(b"RIFF")

    manifest = ChapterManifest(
        source_media_path=workspace.source_dir / "source.webm",
        normalized_audio_path=workspace.normalized_audio_path,
        segment_length=600,
        total_duration=1200.0,
        chapters=[
            Chapter(
                chapter_number=1,
                start=0.0,
                end=600.0,
                duration=600.0,
                file=chapter_one,
            ),
            Chapter(
                chapter_number=2,
                start=600.0,
                end=1200.0,
                duration=600.0,
                file=chapter_two,
            ),
        ],
    )
    workspace.chapter_manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return workspace
