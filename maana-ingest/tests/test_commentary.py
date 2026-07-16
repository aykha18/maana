from __future__ import annotations

import json
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

import pytest
import typer
from typer.testing import CliRunner

from maana_ingest.annotation.models import AnnotationEvidence, AnnotationHit, AnnotationManifest, MergedChapterAnnotation
from maana_ingest.cleaning.models import (
    CleanedChapterTranscript,
    CleanedTranscriptDocument,
    CleanedTranscriptSegment,
)
from maana_ingest.cli import app
from maana_ingest.cli.app import _build_commentary_export_service
from maana_ingest.download import LectureWorkspace
from maana_ingest.exporters import CommentaryExportService, CommentaryJsonExporter
from maana_ingest.models import SourceMetadata
from maana_ingest.ontology import (
    CuratorClaimDecision,
    CuratorOntologyDecision,
    LectureCommentaryComposer,
    LectureCuratorReviewService,
    OntologyReadinessService,
)
from maana_ingest.ontology.commentary import _build_optional_sections
from maana_ingest.ontology.commentary_models import (
    ChapterCommentaryArtifact,
    CommentaryClaimRef,
    CommentaryHeader,
    CoreExplanationBlock,
    EvidencePostureBlock,
    OntologyLinksBlock,
    ProvenanceBlock,
    SourceReferenceBlock,
    StatusAndDisagreementBlock,
)


def test_commentary_composer_writes_json_and_markdown_for_approved_claims(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(tmp_path)
    registry_path = _copy_registry(tmp_path)
    settings = SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)

    readiness = OntologyReadinessService(settings=settings)
    manifest = readiness.initialize_knowledge_manifest(workspace.lecture_root)

    review_service = LectureCuratorReviewService(settings=settings)
    review = review_service.generate_review_file(manifest.manifest_path)
    payload = json.loads(review.review_path.read_text(encoding="utf-8"))

    payload["items"][0]["decision"] = CuratorClaimDecision.APPROVE.value
    payload["items"][0]["reviewed_truth_status"] = "supported"
    payload["items"][0]["reviewed_by"] = "curator.demo"
    payload["items"][1]["decision"] = CuratorClaimDecision.APPROVE.value
    payload["items"][1]["reviewed_truth_status"] = "supported"
    payload["items"][1]["reviewed_by"] = "curator.demo"
    payload["items"][1]["reviewed_interpretation_mode"] = "philosophical"
    payload["items"][1]["ontology_reviews"][0]["decision"] = CuratorOntologyDecision.CREATE_NEW.value
    payload["items"][1]["ontology_reviews"][0]["approved_label"] = "Shibli"

    review.review_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    review_service.apply_review_file(review.review_path)

    composer = LectureCommentaryComposer(settings=settings)
    result = composer.compose_from_manifest(manifest.manifest_path)

    assert result.composed_chapters == 1
    chapter_dir = workspace.knowledge_chapters_dir / "chapter-001"
    assert chapter_dir.joinpath("commentary.json").exists()
    assert chapter_dir.joinpath("commentary.md").exists()

    json_payload = json.loads(chapter_dir.joinpath("commentary.json").read_text(encoding="utf-8"))
    assert json_payload["header"]["commentary_type"] == "canonical_commentary"
    assert json_payload["header"]["scope_kind"] == "lecture_chapter"
    assert json_payload["source_references"]["cited_unit_refs"] == ["lecture-chapter:001"]
    assert json_payload["core_explanation"]["claim_count"] == 2
    assert json_payload["core_explanation"]["claims"][0]["interpretation_mode"] == "literal"
    assert json_payload["core_explanation"]["claims"][1]["interpretation_mode"] == "philosophical"
    assert "author.shibli" in json_payload["ontology_links"]["canonical_ontology_ids"]
    section_keys = {section["section_key"] for section in json_payload["optional_sections"]}
    assert "literal_clarification" in section_keys
    assert "interpretive_reading" in section_keys
    assert "comparative_references" not in section_keys
    assert json_payload["evidence_posture"]["overall_evidence_posture"] == "directly_evidenced"
    assert json_payload["provenance"]["ai_involvement"] is True
    assert json_payload["status_and_disagreement"]["editorial_state"] == "approved"

    markdown = chapter_dir.joinpath("commentary.md").read_text(encoding="utf-8")
    assert "## Commentary Header" in markdown
    assert "## Core Explanation Block" in markdown
    assert "## Optional Commentary Sections" in markdown
    assert "### Literal Clarification" in markdown
    assert "### Interpretive Reading" in markdown
    assert "Comparative References" not in markdown
    assert "## Status And Disagreement Block" in markdown
    assert "- Interpretation mode: literal" in markdown
    assert "- Interpretation mode: philosophical" in markdown
    assert "author.shibli" in markdown


def test_commentary_export_service_writes_json_and_markdown(tmp_path: Path) -> None:
    artifact = ChapterCommentaryArtifact(
        lecture_root=tmp_path,
        chapter_number=1,
        output_json_path=tmp_path / "commentary.json",
        output_markdown_path=tmp_path / "commentary.md",
        header=CommentaryHeader(
            commentary_id="chapter-commentary:001",
            commentary_type="canonical_commentary",
            scope_kind="lecture_chapter",
            scope_reference="lecture-chapter:001",
            contributor_classes=["ai_system"],
            editorial_state="approved",
            approval_scope="editorial",
        ),
        source_references=SourceReferenceBlock(
            source_cleaned_path=tmp_path / "cleaned.json",
            source_claim_bundle_path=tmp_path / "claim_bundle.json",
            cited_unit_refs=["lecture-chapter:001"],
        ),
        core_explanation=CoreExplanationBlock(
            summary="A governed summary.",
            claim_count=1,
            claims=[
                CommentaryClaimRef(
                    claim_id="claim-001",
                    statement="A governed claim.",
                    claim_type="textual",
                    interpretation_mode="literal",
                    source_stage="annotation",
                    evidence_posture="directly_evidenced",
                    truth_status="supported",
                )
            ],
        ),
        evidence_posture=EvidencePostureBlock(
            overall_evidence_posture="directly_evidenced",
            claim_postures=["directly_evidenced"],
        ),
        provenance=ProvenanceBlock(
            contributor_classes=["ai_system"],
            methods=["specialized_annotation_analyzer"],
            source_stages=["annotation"],
            reviewers=["curator.demo"],
            ai_involvement=True,
        ),
        ontology_links=OntologyLinksBlock(canonical_ontology_ids=["author.shibli"]),
        status_and_disagreement=StatusAndDisagreementBlock(
            editorial_state="approved",
            truth_statuses=["supported"],
            has_contested_claims=False,
            has_ai_generated_content=True,
            notes=[],
        ),
    )

    service = CommentaryExportService()
    output_paths = service.export(artifact)

    assert artifact.output_json_path in output_paths
    assert artifact.output_markdown_path in output_paths
    assert json.loads(artifact.output_json_path.read_text(encoding="utf-8"))["header"]["commentary_id"] == (
        "chapter-commentary:001"
    )
    markdown = artifact.output_markdown_path.read_text(encoding="utf-8")
    assert "## Commentary Header" in markdown
    assert "- Interpretation mode: literal" in markdown
    assert "author.shibli" in markdown


def test_commentary_composer_supports_json_only_export(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(tmp_path)
    registry_path = _copy_registry(tmp_path)
    settings = SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)

    readiness = OntologyReadinessService(settings=settings)
    manifest = readiness.initialize_knowledge_manifest(workspace.lecture_root)

    review_service = LectureCuratorReviewService(settings=settings)
    review = review_service.generate_review_file(manifest.manifest_path)
    payload = json.loads(review.review_path.read_text(encoding="utf-8"))
    payload["items"][0]["decision"] = CuratorClaimDecision.APPROVE.value
    payload["items"][0]["reviewed_truth_status"] = "supported"
    payload["items"][1]["decision"] = CuratorClaimDecision.APPROVE.value
    payload["items"][1]["reviewed_truth_status"] = "supported"
    payload["items"][1]["ontology_reviews"][0]["decision"] = CuratorOntologyDecision.CREATE_NEW.value
    payload["items"][1]["ontology_reviews"][0]["approved_label"] = "Shibli"
    review.review_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    review_service.apply_review_file(review.review_path)

    export_service = CommentaryExportService(exporters=[CommentaryJsonExporter()])
    composer = LectureCommentaryComposer(settings=settings, export_service=export_service)

    first_result = composer.compose_from_manifest(manifest.manifest_path)
    second_result = composer.compose_from_manifest(manifest.manifest_path)

    chapter_dir = workspace.knowledge_chapters_dir / "chapter-001"
    assert chapter_dir.joinpath("commentary.json").exists()
    assert not chapter_dir.joinpath("commentary.md").exists()
    assert first_result.chapter_artifacts == [chapter_dir / "commentary.json"]
    assert second_result.composed_chapters == 0
    assert second_result.skipped_chapters == 1
    assert second_result.chapter_artifacts == [chapter_dir / "commentary.json"]


def test_build_commentary_export_service_rejects_unknown_format() -> None:
    with pytest.raises(typer.BadParameter):
        _build_commentary_export_service(["html"])


def test_optional_sections_prefer_interpretation_mode_over_claim_type() -> None:
    sections = _build_optional_sections(
        [
            CommentaryClaimRef(
                claim_id="claim-001",
                statement="The reference is used philosophically rather than comparatively.",
                claim_type="referential",
                interpretation_mode="philosophical",
                source_stage="annotation",
                evidence_posture="plausibly_supported",
                truth_status="supported",
            )
        ]
    )

    section_keys = {section.section_key for section in sections}
    assert "interpretive_reading" in section_keys
    assert "comparative_references" not in section_keys


def test_commentary_composer_uses_extracted_interpretation_mode_defaults(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(
        tmp_path,
        couplet_hints=["symbolic"],
        couplet_notes="Fallback note should not be needed when hints exist.",
        poet_hints=["philosophical"],
        poet_notes="Fallback note should not be needed when hints exist.",
    )
    registry_path = _copy_registry(tmp_path)
    settings = SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)

    readiness = OntologyReadinessService(settings=settings)
    manifest = readiness.initialize_knowledge_manifest(workspace.lecture_root)

    review_service = LectureCuratorReviewService(settings=settings)
    review = review_service.generate_review_file(manifest.manifest_path)
    payload = json.loads(review.review_path.read_text(encoding="utf-8"))

    payload["items"][0]["decision"] = CuratorClaimDecision.APPROVE.value
    payload["items"][0]["reviewed_truth_status"] = "supported"
    payload["items"][1]["decision"] = CuratorClaimDecision.APPROVE.value
    payload["items"][1]["reviewed_truth_status"] = "supported"
    payload["items"][1]["ontology_reviews"][0]["decision"] = CuratorOntologyDecision.CREATE_NEW.value
    payload["items"][1]["ontology_reviews"][0]["approved_label"] = "Shibli"
    review.review_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    review_service.apply_review_file(review.review_path)

    composer = LectureCommentaryComposer(settings=settings)
    composer.compose_from_manifest(manifest.manifest_path)

    chapter_dir = workspace.knowledge_chapters_dir / "chapter-001"
    json_payload = json.loads(chapter_dir.joinpath("commentary.json").read_text(encoding="utf-8"))
    claim_modes = [claim["interpretation_mode"] for claim in json_payload["core_explanation"]["claims"]]
    section_keys = {section["section_key"] for section in json_payload["optional_sections"]}

    assert "symbolic" in claim_modes
    assert "philosophical" in claim_modes
    assert "literal_clarification" not in section_keys
    assert "interpretive_reading" in section_keys


def test_compose_lecture_commentary_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

    expected = SimpleNamespace(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo",
        knowledge_manifest_path=tmp_path / "knowledge" / "manifest.json",
        composed_chapters=1,
        skipped_chapters=0,
        chapter_artifacts=[tmp_path / "knowledge" / "chapters" / "chapter-001" / "commentary.json"],
    )

    def fake_compose_from_manifest(self: object, knowledge_manifest_path: Path, *, force: bool = False) -> object:
        return expected

    monkeypatch.setattr(LectureCommentaryComposer, "compose_from_manifest", fake_compose_from_manifest)
    result = runner.invoke(app, ["compose-lecture-commentary", str(tmp_path / "knowledge" / "manifest.json")])

    assert result.exit_code == 0
    assert "Composed chapters: 1" in result.stdout
    assert "Artifacts:" in result.stdout


def test_compose_lecture_commentary_cli_supports_json_only_format(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    captured: dict[str, object] = {}

    def fake_init(self: object, settings: object, *, export_service: object | None = None) -> None:
        captured["export_service"] = export_service

    expected = SimpleNamespace(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo",
        knowledge_manifest_path=tmp_path / "knowledge" / "manifest.json",
        composed_chapters=1,
        skipped_chapters=0,
        chapter_artifacts=[tmp_path / "knowledge" / "chapters" / "chapter-001" / "commentary.json"],
    )

    def fake_compose_from_manifest(self: object, knowledge_manifest_path: Path, *, force: bool = False) -> object:
        return expected

    monkeypatch.setattr(LectureCommentaryComposer, "__init__", fake_init)
    monkeypatch.setattr(LectureCommentaryComposer, "compose_from_manifest", fake_compose_from_manifest)
    result = runner.invoke(
        app,
        [
            "compose-lecture-commentary",
            str(tmp_path / "knowledge" / "manifest.json"),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    export_service = captured["export_service"]
    assert isinstance(export_service, CommentaryExportService)
    assert [type(exporter) for exporter in export_service._exporters] == [CommentaryJsonExporter]
    assert str(tmp_path / "knowledge" / "chapters" / "chapter-001" / "commentary.json") in result.stdout
    assert "commentary.md" not in result.stdout


def test_compose_lecture_commentary_cli_rejects_invalid_format(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "compose-lecture-commentary",
            str(tmp_path / "knowledge" / "manifest.json"),
            "--format",
            "html",
        ],
    )

    assert result.exit_code != 0
    assert "Unsupported commentary export format: html" in result.stdout


def _create_annotated_workspace(
    base_dir: Path,
    *,
    couplet_hints: list[str] | None = None,
    couplet_notes: str | None = None,
    poet_hints: list[str] | None = None,
    poet_notes: str | None = None,
) -> LectureWorkspace:
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
        couplets=[
            AnnotationHit(
                label="quoted-couplet",
                text="دل ہی تو ہے نہ سنگ و خشت",
                interpretation_hints=couplet_hints or [],
                notes=couplet_notes,
                confidence=0.91,
                evidence=[AnnotationEvidence(start=0.0, end=2.0, excerpt="دل ہی تو ہے")],
            )
        ],
        poets=[
            AnnotationHit(
                label="Shibli",
                text="شبلی",
                interpretation_hints=poet_hints or [],
                notes=poet_notes,
                confidence=0.95,
                evidence=[AnnotationEvidence(start=0.0, end=2.0, excerpt="شبلی")],
            )
        ],
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


def _copy_registry(base_dir: Path) -> Path:
    target = base_dir / "canonical_registry.json"
    copyfile(_repo_registry_path(), target)
    return target


def _repo_registry_path() -> Path:
    return Path(__file__).resolve().parents[1] / "registry" / "canonical_registry.json"
