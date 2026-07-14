from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.annotation import AnnotationResult, AnnotationService
from maana_ingest.annotation.client import AnnotationLLMClient, AnnotationRequest
from maana_ingest.cleaning.models import (
    CleanedChapterTranscript,
    CleanedTranscriptDocument,
    CleanedTranscriptSegment,
)
from maana_ingest.cli import app
from maana_ingest.download import LectureWorkspace
from maana_ingest.models import SourceMetadata


class FakeAnnotationClient:
    provider_name = "mock"
    model_name = "fake-model"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def annotate_json(self, request: AnnotationRequest) -> dict[str, object]:
        self.calls.append(request.analyzer_name)
        if request.analyzer_name == "couplet_detector":
            return {
                "couplets": [
                    {
                        "label": "quoted-couplet",
                        "text": "دل ہی تو ہے نہ سنگ و خشت",
                        "confidence": 0.91,
                        "interpretation_hints": ["symbolic"],
                        "evidence": [{"start": 0.0, "end": 2.0, "excerpt": "دل ہی تو ہے"}],
                    }
                ]
            }
        if request.analyzer_name == "quran_detector":
            return {"verses": []}
        if request.analyzer_name == "hadith_detector":
            return {"hadiths": []}
        if request.analyzer_name == "poet_detector":
            return {
                "poets": [
                    {
                        "label": "Ghalib",
                        "text": "غالب",
                        "confidence": 0.95,
                        "interpretation_hints": ["philosophical"],
                        "evidence": [{"start": 0.0, "end": 2.0, "excerpt": "غالب"}],
                    }
                ]
            }
        if request.analyzer_name == "persian_detector":
            return {"passages": []}
        if request.analyzer_name == "citation_resolver":
            return {
                "citations": [
                    {
                        "citation": "دیوان غالب",
                        "resolved_as": "Diwan-e-Ghalib",
                        "citation_type": "book",
                        "confidence": 0.88,
                        "interpretation_hints": ["comparative"],
                        "evidence": [{"start": 0.0, "end": 2.0, "excerpt": "دیوان غالب"}],
                    }
                ]
            }
        raise AssertionError(f"Unexpected analyzer: {request.analyzer_name}")


class FakeAnnotationClientWithoutHints:
    provider_name = "mock"
    model_name = "fake-model"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def annotate_json(self, request: AnnotationRequest) -> dict[str, object]:
        self.calls.append(request.analyzer_name)
        if request.analyzer_name == "couplet_detector":
            return {
                "couplets": [
                    {
                        "label": "quoted-couplet",
                        "text": "دل ہی تو ہے نہ سنگ و خشت",
                        "notes": "Symbolic image of fragility and ruin.",
                        "confidence": 0.91,
                        "evidence": [{"start": 0.0, "end": 2.0, "excerpt": "دل ہی تو ہے"}],
                    }
                ]
            }
        if request.analyzer_name == "quran_detector":
            return {"verses": []}
        if request.analyzer_name == "hadith_detector":
            return {"hadiths": []}
        if request.analyzer_name == "poet_detector":
            return {
                "poets": [
                    {
                        "label": "Ghalib",
                        "text": "غالب",
                        "notes": "Philosophical reflection on being and selfhood.",
                        "confidence": 0.95,
                        "evidence": [{"start": 0.0, "end": 2.0, "excerpt": "غالب"}],
                    }
                ]
            }
        if request.analyzer_name == "persian_detector":
            return {"passages": []}
        if request.analyzer_name == "citation_resolver":
            return {
                "citations": [
                    {
                        "citation": "دیوان غالب",
                        "resolved_as": "Diwan-e-Ghalib",
                        "citation_type": "book",
                        "notes": "Comparative reference to a poetic collection.",
                        "confidence": 0.88,
                        "evidence": [{"start": 0.0, "end": 2.0, "excerpt": "دیوان غالب"}],
                    }
                ]
            }
        raise AssertionError(f"Unexpected analyzer: {request.analyzer_name}")


def test_annotation_service_writes_prompt_outputs_and_manifest(tmp_path: Path) -> None:
    workspace = _create_cleaned_workspace(tmp_path)
    fake_client = FakeAnnotationClient()
    settings = SimpleNamespace(annotation_prompt_version="v1")

    service = AnnotationService(settings=settings, client=fake_client)
    result = service.annotate_lecture(workspace.lecture_root)

    assert result.completed_chapters == 1
    assert result.skipped_chapters == 0
    assert result.chapter_count == 1
    assert len(fake_client.calls) == 6
    assert workspace.annotation_manifest_path.exists()

    chapter_dir = workspace.annotation_chapters_dir / "chapter-001"
    assert chapter_dir.joinpath("couplet_detector.json").exists()
    assert chapter_dir.joinpath("couplet_detector.raw.json").exists()
    assert chapter_dir.joinpath("merged.json").exists()
    assert chapter_dir.joinpath("prompts", "couplet_detector-v1.md").exists()

    merged_payload = json.loads(chapter_dir.joinpath("merged.json").read_text(encoding="utf-8"))
    assert merged_payload["couplets"][0]["label"] == "quoted-couplet"
    assert merged_payload["couplets"][0]["interpretation_hints"] == ["symbolic"]
    assert merged_payload["poets"][0]["label"] == "Ghalib"
    assert merged_payload["poets"][0]["interpretation_hints"] == ["philosophical"]
    assert merged_payload["citations"][0]["resolved_as"] == "Diwan-e-Ghalib"
    assert merged_payload["citations"][0]["interpretation_hints"] == ["comparative"]

    second = service.annotate_lecture(workspace.lecture_root)
    assert second.completed_chapters == 0
    assert second.skipped_chapters == 1
    assert len(fake_client.calls) == 6


def test_annotation_service_enriches_missing_interpretation_hints(tmp_path: Path) -> None:
    workspace = _create_cleaned_workspace(tmp_path)
    fake_client = FakeAnnotationClientWithoutHints()
    settings = SimpleNamespace(annotation_prompt_version="v1")

    service = AnnotationService(settings=settings, client=fake_client)
    service.annotate_lecture(workspace.lecture_root)

    merged_payload = json.loads(
        workspace.annotation_chapters_dir.joinpath("chapter-001", "merged.json").read_text(encoding="utf-8")
    )
    assert merged_payload["couplets"][0]["interpretation_hints"] == ["symbolic"]
    assert merged_payload["poets"][0]["interpretation_hints"] == ["philosophical"]
    assert merged_payload["citations"][0]["interpretation_hints"] == ["comparative"]


def test_annotate_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = AnnotationResult(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        annotation_manifest_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "annotations" / "manifest.json",
        provider="mock",
        model_name="fake-model",
        prompt_version="v1",
        completed_chapters=1,
        skipped_chapters=0,
        chapter_count=1,
    )

    def fake_annotate_lecture(
        self: object,
        lecture_path: Path,
        *,
        force: bool = False,
        progress_callback: object = None,
    ) -> AnnotationResult:
        return expected

    monkeypatch.setattr(AnnotationService, "annotate_lecture", fake_annotate_lecture)

    result = runner.invoke(app, ["annotate", str(tmp_path)])

    assert result.exit_code == 0
    assert "Annotation manifest:" in result.stdout
    assert "Prompt version: v1" in result.stdout
    assert "Chapter count: 1" in result.stdout


def _create_cleaned_workspace(base_dir: Path) -> LectureWorkspace:
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

    document = CleanedTranscriptDocument(
        lecture_root=workspace.lecture_root,
        transcription_manifest_path=workspace.transcription_manifest_path,
        cleaned_json_path=workspace.cleaned_transcript_json_path,
        cleaned_markdown_path=workspace.cleaned_transcript_markdown_path,
        total_chapters=1,
        total_segments=2,
        merged_segment_count=0,
        chapters=[
            CleanedChapterTranscript(
                chapter_number=1,
                language="ur",
                source_audio_path=workspace.chapters_dir / "chapter-001.wav",
                raw_transcript_path=workspace.transcript_chapters_dir / "chapter-001" / "transcript.json",
                cleaned_text="غالب دیوان غالب کا شعر پڑھتے ہیں",
                original_text="غالب دیوان غالب کا شعر پڑھتے ہیں",
                segments=[
                    CleanedTranscriptSegment(
                        chapter_number=1,
                        start=0.0,
                        end=2.0,
                        original_text="غالب دیوان غالب کا شعر پڑھتے ہیں",
                        cleaned_text="غالب دیوان غالب کا شعر پڑھتے ہیں",
                        original_segment_ids=[0],
                    )
                ],
            )
        ],
    )
    workspace.cleaned_transcript_json_path.write_text(
        json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    workspace.cleaned_transcript_markdown_path.write_text("# Clean Transcript\n", encoding="utf-8")
    return workspace
