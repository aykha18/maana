from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.cleaning import CleaningResult, TranscriptCleaningService
from maana_ingest.cleaning.service import normalize_transcript_text
from maana_ingest.cli import app
from maana_ingest.download import LectureWorkspace
from maana_ingest.models import SourceMetadata
from maana_ingest.speech.models import ChapterTranscript, TranscriptionManifest


def test_normalize_transcript_text_handles_urdu_punctuation() -> None:
    text = "یہ ایک سوال ہے ? اور یہ ، ایک مثال ہے ."
    assert normalize_transcript_text(text) == "یہ ایک سوال ہے؟ اور یہ، ایک مثال ہے۔"


def test_cleaning_service_writes_clean_json_and_markdown(tmp_path: Path) -> None:
    workspace = _create_transcribed_workspace(tmp_path)
    settings = SimpleNamespace(clean_merge_gap_seconds=1.5)

    service = TranscriptCleaningService(settings=settings)
    result = service.clean_transcripts(workspace.lecture_root)

    assert result.total_chapters == 1
    assert result.total_segments == 2
    assert result.merged_segment_count == 1
    assert result.cleaned_json_path.exists()
    assert result.cleaned_markdown_path.exists()

    payload = json.loads(result.cleaned_json_path.read_text(encoding="utf-8"))
    assert payload["total_chapters"] == 1
    assert payload["merged_segment_count"] == 1
    first_segment = payload["chapters"][0]["segments"][0]
    assert first_segment["original_segment_ids"] == [0, 1]
    assert first_segment["cleaned_text"] == "یہ ایک سوال ہے اور جواب بھی موجود ہے"

    markdown = result.cleaned_markdown_path.read_text(encoding="utf-8")
    assert "# Clean Transcript" in markdown
    assert "## Chapter 1" in markdown


def test_clean_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = CleaningResult(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        cleaned_json_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "cleaned" / "transcript.json",
        cleaned_markdown_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "cleaned" / "clean_transcript.md",
        total_chapters=1,
        total_segments=2,
        merged_segment_count=1,
    )

    def fake_clean_transcripts(
        self: object,
        lecture_path: Path,
        *,
        force: bool = False,
    ) -> CleaningResult:
        return expected

    monkeypatch.setattr(TranscriptCleaningService, "clean_transcripts", fake_clean_transcripts)

    result = runner.invoke(app, ["clean", str(tmp_path)])

    assert result.exit_code == 0
    assert "Clean JSON:" in result.stdout
    assert "Merged segments: 1" in result.stdout


def _create_transcribed_workspace(base_dir: Path) -> LectureWorkspace:
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

    chapter_dir = workspace.transcript_chapters_dir / "chapter-001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    raw_json_path = chapter_dir / "transcript.json"
    raw_json_path.write_text(
        json.dumps(
            {
                "chapter_number": 1,
                "source_audio_path": str((workspace.chapters_dir / "chapter-001.wav").resolve()),
                "language": "ur",
                "text": "یہ ایک سوال ہے\nاور جواب بھی موجود ہے",
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 1.2,
                        "text": "یہ ایک سوال ہے",
                    },
                    {
                        "id": 1,
                        "start": 1.3,
                        "end": 2.5,
                        "text": "اور جواب بھی موجود ہے",
                    },
                    {
                        "id": 2,
                        "start": 4.5,
                        "end": 5.5,
                        "text": "یہ الگ جملہ ہے .",
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    transcription_manifest = TranscriptionManifest(
        lecture_root=workspace.lecture_root,
        transcripts_dir=workspace.transcripts_dir,
        model_name="tiny",
        device="cpu",
        compute_type="int8",
        beam_size=3,
        requested_language="ur",
        completed_chapters=1,
        skipped_chapters=0,
        chapter_transcripts=[
            ChapterTranscript(
                chapter_number=1,
                source_audio_path=workspace.chapters_dir / "chapter-001.wav",
                raw_json_path=raw_json_path,
                text_path=chapter_dir / "transcript.txt",
                srt_path=chapter_dir / "transcript.srt",
                vtt_path=chapter_dir / "transcript.vtt",
                language="ur",
                text="یہ ایک سوال ہے\nاور جواب بھی موجود ہے\nیہ الگ جملہ ہے .",
                segment_count=3,
            )
        ],
    )
    workspace.transcription_manifest_path.write_text(
        json.dumps(transcription_manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return workspace
