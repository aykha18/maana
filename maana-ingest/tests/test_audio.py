from __future__ import annotations

import json
import wave
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.audio import AudioPreparationResult, AudioPreparationService
from maana_ingest.cli import app
from maana_ingest.download import LectureWorkspace
from maana_ingest.models import SourceMetadata


def test_audio_preparation_creates_normalized_audio_and_manifest(tmp_path: Path, monkeypatch) -> None:
    workspace = _create_workspace_with_source(tmp_path)
    settings = SimpleNamespace(
        ffmpeg_binary="ffmpeg",
        audio_sample_rate=16000,
        audio_channels=1,
        trim_silence=False,
        segment_length=2,
    )
    commands: list[list[str]] = []

    def fake_which(binary: str) -> str:
        return f"C:/tools/{binary}.exe"

    def fake_ffmpeg_runner(command: list[str]) -> None:
        commands.append(command)
        if command[-1].endswith("normalized.wav"):
            _write_wav(Path(command[-1]), seconds=5)

    monkeypatch.setattr("maana_ingest.audio.service.shutil.which", fake_which)
    service = AudioPreparationService(settings=settings, ffmpeg_runner=fake_ffmpeg_runner)

    result = service.prepare_audio(workspace.lecture_root)

    assert result.normalized_audio_path.exists()
    assert result.chapter_manifest_path.exists()
    assert len(result.chapters) == 3
    assert result.chapters[0].duration == 2.0
    assert result.chapters[2].duration == 1.0
    assert commands[0] == ["ffmpeg", "-version"]
    assert commands[1][0] == "ffmpeg"

    manifest = json.loads(result.chapter_manifest_path.read_text(encoding="utf-8"))
    assert manifest["segment_length"] == 2
    assert len(manifest["chapters"]) == 3


def test_split_cli_reports_generated_outputs(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = AudioPreparationResult(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        source_media_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "source" / "source.m4a",
        normalized_audio_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "audio" / "normalized.wav",
        chapter_manifest_path=tmp_path
        / "lectures"
        / "speaker"
        / "demo123-title"
        / "audio"
        / "chapters"
        / "manifest.json",
        chapters=[],
        ffmpeg_binary="ffmpeg",
    )

    def fake_prepare_audio(
        self: object,
        lecture_path: Path,
        *,
        trim_silence: bool | None = None,
        segment_length: int | None = None,
    ) -> AudioPreparationResult:
        return expected

    monkeypatch.setattr(AudioPreparationService, "prepare_audio", fake_prepare_audio)

    result = runner.invoke(app, ["split", str(tmp_path)])

    assert result.exit_code == 0
    assert "Normalized audio:" in result.stdout
    assert "Chapter count: 0" in result.stdout


def _create_workspace_with_source(base_dir: Path) -> LectureWorkspace:
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
    workspace.source_dir.joinpath("source.m4a").write_text("raw-audio", encoding="utf-8")
    return workspace


def _write_wav(path: Path, *, seconds: int, sample_rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = seconds * sample_rate
    silence = b"\x00\x00" * frame_count
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(silence)
