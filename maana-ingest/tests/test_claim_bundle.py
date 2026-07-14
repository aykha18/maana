from __future__ import annotations

from pathlib import Path

from maana_ingest.annotation.models import AnnotationEvidence, AnnotationHit, CitationHit, MergedChapterAnnotation
from maana_ingest.ontology import (
    CanonicalEntityType,
    ClaimBundleBuilder,
    ClaimType,
    EvidencePosture,
    InterpretationMode,
    KnowledgeReviewStatus,
)


def test_claim_bundle_builder_converts_annotation_outputs_to_governed_claims(tmp_path: Path) -> None:
    builder = ClaimBundleBuilder()
    source_cleaned_path = tmp_path / "cleaned" / "transcript.json"
    source_annotation_path = tmp_path / "annotations" / "chapters" / "chapter-001" / "merged.json"
    bundle_path = tmp_path / "knowledge" / "chapters" / "chapter-001" / "claim_bundle.json"

    chapter = MergedChapterAnnotation(
        chapter_number=1,
        source_cleaned_path=source_cleaned_path,
        merged_output_path=source_annotation_path,
        poets=[
            AnnotationHit(
                label="Ghalib",
                text="غالب",
                confidence=0.94,
                evidence=[AnnotationEvidence(start=1.0, end=2.0, excerpt="غالب")],
            )
        ],
        citations=[
            CitationHit(
                citation="دیوان غالب",
                resolved_as="Diwan-e-Ghalib",
                citation_type="book",
                confidence=0.82,
                evidence=[AnnotationEvidence(start=2.0, end=3.0, excerpt="دیوان غالب")],
            )
        ],
    )

    bundle = builder.build_for_chapter(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo",
        source_cleaned_path=source_cleaned_path,
        source_annotation_path=source_annotation_path,
        bundle_path=bundle_path,
        chapter=chapter,
        provider="openai",
        prompt_version="v1",
        model_name="gpt-4.1-mini",
    )

    assert bundle.review_status == KnowledgeReviewStatus.PENDING_REVIEW
    assert bundle.claim_count == 2
    assert bundle.claims[0].claim_type == ClaimType.REFERENTIAL
    assert bundle.claims[0].interpretation_mode == InterpretationMode.COMPARATIVE
    assert bundle.claims[0].evidence_posture == EvidencePosture.DIRECTLY_EVIDENCED
    assert bundle.claims[0].ontology_candidates[0].entity_type == CanonicalEntityType.AUTHOR
    assert bundle.claims[1].ontology_candidates[0].entity_type == CanonicalEntityType.COLLECTION
    assert bundle.claims[1].interpretation_mode == InterpretationMode.COMPARATIVE
    assert bundle.claims[1].statement.endswith("Resolved as: Diwan-e-Ghalib")
    assert bundle.claims[0].provenance[0].source_path == source_annotation_path


def test_claim_bundle_builder_enriches_interpretation_mode_from_annotation_notes(tmp_path: Path) -> None:
    builder = ClaimBundleBuilder()
    source_cleaned_path = tmp_path / "cleaned" / "transcript.json"
    source_annotation_path = tmp_path / "annotations" / "chapters" / "chapter-001" / "merged.json"
    bundle_path = tmp_path / "knowledge" / "chapters" / "chapter-001" / "claim_bundle.json"

    chapter = MergedChapterAnnotation(
        chapter_number=1,
        source_cleaned_path=source_cleaned_path,
        merged_output_path=source_annotation_path,
        couplets=[
            AnnotationHit(
                label="quoted-couplet",
                text="دل ہی تو ہے نہ سنگ و خشت",
                interpretation_hints=[InterpretationMode.SYMBOLIC],
                notes="Literal transcription exists, but structured hint should win.",
                confidence=0.91,
                evidence=[AnnotationEvidence(start=0.0, end=2.0, excerpt="دل ہی تو ہے")],
            )
        ],
        poets=[
            AnnotationHit(
                label="Ghalib",
                text="غالب",
                interpretation_hints=[InterpretationMode.PHILOSOPHICAL],
                notes="Comparative reference exists, but structured hint should win.",
                confidence=0.94,
                evidence=[AnnotationEvidence(start=1.0, end=2.0, excerpt="غالب")],
            )
        ],
    )

    bundle = builder.build_for_chapter(
        lecture_root=tmp_path / "lectures" / "speaker" / "demo",
        source_cleaned_path=source_cleaned_path,
        source_annotation_path=source_annotation_path,
        bundle_path=bundle_path,
        chapter=chapter,
        provider="openai",
        prompt_version="v1",
        model_name="gpt-4.1-mini",
    )

    assert bundle.claims[0].interpretation_mode == InterpretationMode.SYMBOLIC
    assert bundle.claims[1].interpretation_mode == InterpretationMode.PHILOSOPHICAL
