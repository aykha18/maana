from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.annotation.models import AnnotationManifest, MergedChapterAnnotation
from maana_ingest.cleaning.models import (
    CleanedChapterTranscript,
    CleanedTranscriptDocument,
    CleanedTranscriptSegment,
)
from maana_ingest.cli import app
from maana_ingest.download import LectureWorkspace
from maana_ingest.models import SourceMetadata
from maana_ingest.ontology import OntologyReadinessService, ReadinessAssessment


def test_assessment_blocks_canonical_ingestion_without_registry_or_curator(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(tmp_path)
    settings = SimpleNamespace(annotation_provider="openai", canonical_registry_path=None)

    service = OntologyReadinessService(settings=settings)
    assessment = service.assess_lecture(workspace.lecture_root)

    assert assessment.can_start_artifact_ingestion is True
    assert assessment.can_start_knowledge_ingestion is False
    assert assessment.curator_ui_ready is False
    assert "canonical registry" in " ".join(assessment.blockers).lower()
    assert "curator ui" in " ".join(assessment.blockers).lower()


def test_initialize_knowledge_manifest_bootstraps_draft_files(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(tmp_path)
    registry_path = tmp_path / "canonical-registry.json"
    registry_path.write_text("{}", encoding="utf-8")
    settings = SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)

    service = OntologyReadinessService(settings=settings)
    manifest = service.initialize_knowledge_manifest(workspace.lecture_root)

    assert manifest.total_chapters == 1
    assert manifest.chapters_pending_review == 1
    assert manifest.ready_for_canonical_ingestion is False
    assert workspace.knowledge_manifest_path.exists()
    assert workspace.knowledge_chapters_dir.joinpath("chapter-001", "draft.json").exists()


def test_assess_cli_reports_readiness(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = ReadinessAssessment(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        can_start_artifact_ingestion=True,
        can_start_knowledge_ingestion=False,
        curator_ui_ready=False,
        annotation_provider="mock",
        available_artifacts={"cleaned_transcript": True, "annotation_manifest": True},
        blockers=["Curator UI is not implemented."],
        next_tasks=["Build curator workflows."],
        summary="Artifact ingestion can continue, but canonical knowledge ingestion must remain gated.",
    )

    def fake_assess(self: object, lecture_path: Path) -> ReadinessAssessment:
        return expected

    monkeypatch.setattr(OntologyReadinessService, "assess_lecture", fake_assess)

    result = runner.invoke(app, ["assess", str(tmp_path)])

    assert result.exit_code == 0
    assert "Artifact ingestion ready: True" in result.stdout
    assert "Knowledge ingestion ready: False" in result.stdout
    assert "Curator UI ready: False" in result.stdout
    assert "Blockers:" in result.stdout


def _create_annotated_workspace(base_dir: Path) -> LectureWorkspace:
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

    workspace.metadata_path.write_text(
        json.dumps(metadata.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    workspace.source_request_path.write_text("{}", encoding="utf-8")
    workspace.source_dir.joinpath("source.webm").write_text("media", encoding="utf-8")
    workspace.chapter_manifest_path.write_text("{}", encoding="utf-8")
    workspace.transcription_manifest_path.write_text("{}", encoding="utf-8")

    document = CleanedTranscriptDocument(
        lecture_root=workspace.lecture_root,
        transcription_manifest_path=workspace.transcription_manifest_path,
        cleaned_json_path=workspace.cleaned_transcript_json_path,
        cleaned_markdown_path=workspace.cleaned_transcript_markdown_path,
        total_chapters=1,
        total_segments=1,
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

    chapter_dir = workspace.annotation_chapters_dir / "chapter-001"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    merged_output_path = chapter_dir / "merged.json"
    merged = MergedChapterAnnotation(
        chapter_number=1,
        source_cleaned_path=workspace.cleaned_transcript_json_path,
        merged_output_path=merged_output_path,
    )
    merged_output_path.write_text(
        json.dumps(merged.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    annotation_manifest = AnnotationManifest(
        lecture_root=workspace.lecture_root,
        annotation_dir=workspace.annotation_dir,
        provider="openai",
        model_name="fake-model",
        prompt_version="v1",
        completed_chapters=1,
        skipped_chapters=0,
        chapters=[merged],
    )
    workspace.annotation_manifest_path.write_text(
        json.dumps(annotation_manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return workspace
