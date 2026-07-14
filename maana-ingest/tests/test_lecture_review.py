from __future__ import annotations

import json
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.annotation.models import (
    AnnotationEvidence,
    AnnotationHit,
    AnnotationManifest,
    CitationHit,
    MergedChapterAnnotation,
)
from maana_ingest.cleaning.models import (
    CleanedChapterTranscript,
    CleanedTranscriptDocument,
    CleanedTranscriptSegment,
)
from maana_ingest.cli import app
from maana_ingest.download import LectureWorkspace
from maana_ingest.models import SourceMetadata
from maana_ingest.ontology import (
    ApplyLectureClaimReviewResult,
    CuratorClaimDecision,
    CuratorOntologyDecision,
    LectureClaimReviewResult,
    LectureCuratorReviewService,
    OntologyReadinessService,
)


def test_generate_lecture_review_file_collects_claim_bundle_items(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(tmp_path, poet_label="Shibli", collection_label="Majmua-e-Asrar")
    registry_path = _copy_registry(tmp_path)
    readiness_service = OntologyReadinessService(
        settings=SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)
    )
    manifest = readiness_service.initialize_knowledge_manifest(workspace.lecture_root)

    review_service = LectureCuratorReviewService(
        settings=SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)
    )
    result = review_service.generate_review_file(manifest.manifest_path)

    payload = json.loads(result.review_path.read_text(encoding="utf-8"))
    assert result.total_items == 3
    assert result.pending_items == 3
    assert payload["items"][1]["ontology_reviews"][0]["submitted_label"] == "Shibli"
    assert payload["items"][2]["ontology_reviews"][0]["submitted_label"] == "Majmua-e-Asrar"


def test_apply_lecture_review_updates_claim_bundle_and_registry(tmp_path: Path) -> None:
    workspace = _create_annotated_workspace(tmp_path, poet_label="Shibli", collection_label="Majmua-e-Asrar")
    registry_path = _copy_registry(tmp_path)
    settings = SimpleNamespace(annotation_provider="openai", canonical_registry_path=registry_path)
    readiness_service = OntologyReadinessService(settings=settings)
    manifest = readiness_service.initialize_knowledge_manifest(workspace.lecture_root)

    review_service = LectureCuratorReviewService(settings=settings)
    review_result = review_service.generate_review_file(manifest.manifest_path)

    review_payload = json.loads(review_result.review_path.read_text(encoding="utf-8"))
    review_payload["items"][0]["decision"] = CuratorClaimDecision.APPROVE.value
    review_payload["items"][0]["reviewed_truth_status"] = "supported"
    review_payload["items"][0]["reviewed_by"] = "curator.demo"

    review_payload["items"][1]["decision"] = CuratorClaimDecision.APPROVE.value
    review_payload["items"][1]["reviewed_truth_status"] = "supported"
    review_payload["items"][1]["ontology_reviews"][0]["decision"] = CuratorOntologyDecision.CREATE_NEW.value
    review_payload["items"][1]["ontology_reviews"][0]["approved_label"] = "Shibli"
    review_payload["items"][1]["ontology_reviews"][0]["description"] = "Pilot author entity approved from lecture review."

    review_payload["items"][2]["decision"] = CuratorClaimDecision.REQUEST_REVISION.value
    review_payload["items"][2]["reviewed_by"] = "curator.demo"
    review_payload["items"][2]["ontology_reviews"][0]["decision"] = CuratorOntologyDecision.REJECT.value
    review_payload["items"][2]["ontology_reviews"][0]["notes"] = "Collection needs more source verification."

    review_result.review_path.write_text(json.dumps(review_payload, indent=2), encoding="utf-8")
    applied = review_service.apply_review_file(review_result.review_path)

    assert applied.approved_claims == 2
    assert applied.revision_requested_claims == 1
    assert applied.ontology_appended_entries == 1
    assert applied.ontology_rejected == 1

    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    assert any(entry["canonical_id"] == "author.shibli" for entry in registry_payload["entries"])

    bundle_payload = json.loads(
        workspace.knowledge_chapters_dir.joinpath("chapter-001", "claim_bundle.json").read_text(encoding="utf-8")
    )
    assert bundle_payload["claims"][0]["review"]["editorial_state"] == "approved"
    assert bundle_payload["claims"][1]["ontology_candidates"][0]["canonical_id"] == "author.shibli"
    assert bundle_payload["claims"][2]["review"]["editorial_state"] == "in_review"
    assert bundle_payload["claims"][2]["ontology_candidates"][0]["mapping_status"] == "unresolved"

    manifest_payload = json.loads(workspace.knowledge_manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["chapters_pending_review"] == 1
    assert manifest_payload["ready_for_canonical_ingestion"] is False


def test_prepare_lecture_review_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = LectureClaimReviewResult(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        review_path=tmp_path / "knowledge" / "manifest.review.json",
        total_items=3,
        pending_items=3,
    )

    def fake_generate_review_file(
        self: object,
        knowledge_manifest_path: Path,
        *,
        output_path: Path | None = None,
    ) -> LectureClaimReviewResult:
        return expected

    monkeypatch.setattr(LectureCuratorReviewService, "generate_review_file", fake_generate_review_file)

    result = runner.invoke(app, ["prepare-lecture-review", str(tmp_path / "knowledge" / "manifest.json")])

    assert result.exit_code == 0
    assert "Total items: 3" in result.stdout
    assert "Pending items: 3" in result.stdout


def test_apply_lecture_review_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = ApplyLectureClaimReviewResult(
        review_path=tmp_path / "knowledge" / "manifest.review.json",
        applied_path=tmp_path / "knowledge" / "manifest.review.applied.json",
        registry_path=tmp_path / "canonical_registry.json",
        approved_claims=2,
        rejected_claims=1,
        revision_requested_claims=1,
        pending_claims=0,
        ontology_appended_entries=1,
        ontology_approved_existing=0,
        ontology_rejected=1,
    )

    def fake_apply_review_file(self: object, review_path: Path) -> ApplyLectureClaimReviewResult:
        return expected

    monkeypatch.setattr(LectureCuratorReviewService, "apply_review_file", fake_apply_review_file)

    result = runner.invoke(app, ["apply-lecture-review", str(tmp_path / "knowledge" / "manifest.review.json")])

    assert result.exit_code == 0
    assert "Applied path:" in result.stdout
    assert "Approved claims: 2" in result.stdout
    assert "Ontology appended entries: 1" in result.stdout


def _create_annotated_workspace(base_dir: Path, *, poet_label: str, collection_label: str) -> LectureWorkspace:
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
                confidence=0.91,
                evidence=[AnnotationEvidence(start=0.0, end=2.0, excerpt="دل ہی تو ہے")],
            )
        ],
        poets=[
            AnnotationHit(
                label=poet_label,
                text=poet_label,
                confidence=0.95,
                evidence=[AnnotationEvidence(start=0.0, end=2.0, excerpt=poet_label)],
            )
        ],
        citations=[
            CitationHit(
                citation=collection_label,
                resolved_as=collection_label,
                citation_type="book",
                confidence=0.88,
                evidence=[AnnotationEvidence(start=0.0, end=2.0, excerpt=collection_label)],
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
