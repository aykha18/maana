"""Governed claim bundle generation from current annotation outputs."""

from __future__ import annotations

from pathlib import Path

from maana_ingest.annotation.models import AnnotationHit, CitationHit, MergedChapterAnnotation
from maana_ingest.ontology.models import (
    ApprovalScope,
    CanonicalEntityCandidate,
    CanonicalEntityType,
    ChapterClaimBundle,
    ClaimEvidence,
    ClaimSubjectKind,
    ClaimSubjectRef,
    ClaimType,
    ContributorKind,
    EditorialState,
    EvidencePosture,
    EvidenceType,
    GovernedClaim,
    KnowledgeReviewStatus,
    ProvenanceRecord,
    ReviewState,
    TruthStatus,
)
from maana_ingest.ontology.resolver import normalize_registry_label


class ClaimBundleBuilder:
    """Convert merged annotation outputs into governed claim bundle scaffolding."""

    def build_for_chapter(
        self,
        *,
        lecture_root: Path,
        source_cleaned_path: Path,
        source_annotation_path: Path,
        bundle_path: Path,
        chapter: MergedChapterAnnotation,
        provider: str,
        prompt_version: str,
        model_name: str,
    ) -> ChapterClaimBundle:
        subject = ClaimSubjectRef(
            kind=ClaimSubjectKind.LECTURE_CHAPTER,
            reference_id=f"lecture-chapter:{chapter.chapter_number:03d}",
            label=f"Lecture chapter {chapter.chapter_number}",
            source_path=source_cleaned_path,
        )
        claims: list[GovernedClaim] = []

        claims.extend(
            self._claims_from_hits(
                hits=chapter.couplets,
                analyzer_name="couplet_detector",
                claim_prefix="couplet",
                claim_type=ClaimType.TEXTUAL,
                statement_prefix="Candidate quoted couplet detected",
                chapter_number=chapter.chapter_number,
                subject=subject,
                prompt_version=prompt_version,
                model_name=model_name,
                source_annotation_path=source_annotation_path,
            )
        )
        claims.extend(
            self._claims_from_hits(
                hits=chapter.quran_references,
                analyzer_name="quran_detector",
                claim_prefix="quran",
                claim_type=ClaimType.REFERENTIAL,
                statement_prefix="Candidate Quran reference detected",
                chapter_number=chapter.chapter_number,
                subject=subject,
                prompt_version=prompt_version,
                model_name=model_name,
                source_annotation_path=source_annotation_path,
            )
        )
        claims.extend(
            self._claims_from_hits(
                hits=chapter.hadith_references,
                analyzer_name="hadith_detector",
                claim_prefix="hadith",
                claim_type=ClaimType.REFERENTIAL,
                statement_prefix="Candidate hadith reference detected",
                chapter_number=chapter.chapter_number,
                subject=subject,
                prompt_version=prompt_version,
                model_name=model_name,
                source_annotation_path=source_annotation_path,
            )
        )
        claims.extend(
            self._claims_from_hits(
                hits=chapter.poets,
                analyzer_name="poet_detector",
                claim_prefix="poet",
                claim_type=ClaimType.REFERENTIAL,
                statement_prefix="Candidate poet reference detected",
                chapter_number=chapter.chapter_number,
                subject=subject,
                prompt_version=prompt_version,
                model_name=model_name,
                source_annotation_path=source_annotation_path,
                entity_type=CanonicalEntityType.AUTHOR,
            )
        )
        claims.extend(
            self._claims_from_hits(
                hits=chapter.persian_passages,
                analyzer_name="persian_detector",
                claim_prefix="persian",
                claim_type=ClaimType.TEXTUAL,
                statement_prefix="Candidate Persian passage detected",
                chapter_number=chapter.chapter_number,
                subject=subject,
                prompt_version=prompt_version,
                model_name=model_name,
                source_annotation_path=source_annotation_path,
            )
        )
        claims.extend(
            self._claims_from_citations(
                citations=chapter.citations,
                chapter_number=chapter.chapter_number,
                subject=subject,
                prompt_version=prompt_version,
                model_name=model_name,
                source_annotation_path=source_annotation_path,
            )
        )

        return ChapterClaimBundle(
            chapter_number=chapter.chapter_number,
            lecture_root=lecture_root,
            bundle_path=bundle_path,
            source_cleaned_path=source_cleaned_path,
            source_annotation_path=source_annotation_path,
            generated_from_provider=provider,
            generated_from_prompt_version=prompt_version,
            claim_count=len(claims),
            review_status=KnowledgeReviewStatus.PENDING_REVIEW,
            claims=claims,
        )

    def _claims_from_hits(
        self,
        *,
        hits: list[AnnotationHit],
        analyzer_name: str,
        claim_prefix: str,
        claim_type: ClaimType,
        statement_prefix: str,
        chapter_number: int,
        subject: ClaimSubjectRef,
        prompt_version: str,
        model_name: str,
        source_annotation_path: Path,
        entity_type: CanonicalEntityType | None = None,
    ) -> list[GovernedClaim]:
        claims: list[GovernedClaim] = []
        for index, hit in enumerate(hits, start=1):
            evidence = [
                ClaimEvidence(
                    evidence_type=EvidenceType.ANNOTATION_HIT,
                    source_stage="annotation",
                    source_path=source_annotation_path,
                    analyzer_name=analyzer_name,
                    label=hit.label,
                    excerpt=item.excerpt,
                    start=item.start,
                    end=item.end,
                    notes=hit.notes,
                )
                for item in hit.evidence
            ]
            provenance = [
                ProvenanceRecord(
                    chapter_number=chapter_number,
                    source_stage="annotation",
                    start=item.start,
                    end=item.end,
                    excerpt=item.excerpt,
                    detector=analyzer_name,
                    prompt_version=prompt_version,
                    contributor_kind=ContributorKind.AI_SYSTEM,
                    method="specialized_annotation_analyzer",
                    model_name=model_name,
                    source_path=source_annotation_path,
                )
                for item in hit.evidence
            ]
            if not provenance:
                provenance.append(
                    ProvenanceRecord(
                        chapter_number=chapter_number,
                        source_stage="annotation",
                        detector=analyzer_name,
                        prompt_version=prompt_version,
                        contributor_kind=ContributorKind.AI_SYSTEM,
                        method="specialized_annotation_analyzer",
                        model_name=model_name,
                        source_path=source_annotation_path,
                    )
                )

            ontology_candidates = []
            if entity_type is not None and hit.label.strip():
                ontology_candidates.append(
                    CanonicalEntityCandidate(
                        entity_type=entity_type,
                        label=hit.label.strip(),
                        normalized_label=normalize_registry_label(hit.label),
                        confidence=hit.confidence,
                        rationale=f"Proposed from {analyzer_name}",
                        provenance=provenance,
                    )
                )

            statement = f"{statement_prefix}: {hit.label}" if hit.label else statement_prefix
            if hit.text.strip():
                statement = f"{statement}. Evidence text: {hit.text.strip()}"

            claims.append(
                GovernedClaim(
                    claim_id=f"chapter-{chapter_number:03d}-{claim_prefix}-{index:03d}",
                    claim_type=claim_type,
                    subject=subject,
                    statement=statement,
                    source_stage="annotation",
                    evidence_posture=(
                        EvidencePosture.DIRECTLY_EVIDENCED if evidence else EvidencePosture.PLAUSIBLY_SUPPORTED
                    ),
                    evidence=evidence,
                    provenance=provenance,
                    review=ReviewState(
                        editorial_state=EditorialState.PROPOSED,
                        truth_status=TruthStatus.SUPPORTED if evidence else TruthStatus.UNRESOLVED,
                        approval_scope=ApprovalScope.EDITORIAL,
                    ),
                    ontology_candidates=ontology_candidates,
                    originating_analyzers=[analyzer_name],
                )
            )
        return claims

    def _claims_from_citations(
        self,
        *,
        citations: list[CitationHit],
        chapter_number: int,
        subject: ClaimSubjectRef,
        prompt_version: str,
        model_name: str,
        source_annotation_path: Path,
    ) -> list[GovernedClaim]:
        claims: list[GovernedClaim] = []
        for index, citation in enumerate(citations, start=1):
            evidence = [
                ClaimEvidence(
                    evidence_type=EvidenceType.CITATION,
                    source_stage="annotation",
                    source_path=source_annotation_path,
                    analyzer_name="citation_resolver",
                    label=citation.resolved_as or citation.citation,
                    excerpt=item.excerpt,
                    start=item.start,
                    end=item.end,
                    notes=citation.notes,
                )
                for item in citation.evidence
            ]
            provenance = [
                ProvenanceRecord(
                    chapter_number=chapter_number,
                    source_stage="annotation",
                    start=item.start,
                    end=item.end,
                    excerpt=item.excerpt,
                    detector="citation_resolver",
                    prompt_version=prompt_version,
                    contributor_kind=ContributorKind.AI_SYSTEM,
                    method="specialized_annotation_analyzer",
                    model_name=model_name,
                    source_path=source_annotation_path,
                )
                for item in citation.evidence
            ]
            if not provenance:
                provenance.append(
                    ProvenanceRecord(
                        chapter_number=chapter_number,
                        source_stage="annotation",
                        detector="citation_resolver",
                        prompt_version=prompt_version,
                        contributor_kind=ContributorKind.AI_SYSTEM,
                        method="specialized_annotation_analyzer",
                        model_name=model_name,
                        source_path=source_annotation_path,
                    )
                )

            ontology_candidates = []
            entity_type = _entity_type_from_citation(citation)
            candidate_label = (citation.resolved_as or citation.citation).strip()
            if entity_type is not None and candidate_label:
                ontology_candidates.append(
                    CanonicalEntityCandidate(
                        entity_type=entity_type,
                        label=candidate_label,
                        normalized_label=normalize_registry_label(candidate_label),
                        confidence=citation.confidence,
                        rationale="Proposed from citation_resolver",
                        provenance=provenance,
                    )
                )

            resolved_text = citation.resolved_as or citation.citation
            claims.append(
                GovernedClaim(
                    claim_id=f"chapter-{chapter_number:03d}-citation-{index:03d}",
                    claim_type=ClaimType.REFERENTIAL,
                    subject=subject,
                    statement=f"Candidate citation detected: {citation.citation}. Resolved as: {resolved_text}",
                    source_stage="annotation",
                    evidence_posture=(
                        EvidencePosture.DIRECTLY_EVIDENCED if evidence else EvidencePosture.PLAUSIBLY_SUPPORTED
                    ),
                    evidence=evidence,
                    provenance=provenance,
                    review=ReviewState(
                        editorial_state=EditorialState.PROPOSED,
                        truth_status=TruthStatus.SUPPORTED if evidence else TruthStatus.UNRESOLVED,
                        approval_scope=ApprovalScope.EDITORIAL,
                    ),
                    ontology_candidates=ontology_candidates,
                    originating_analyzers=["citation_resolver"],
                )
            )
        return claims


def _entity_type_from_citation(citation: CitationHit) -> CanonicalEntityType | None:
    citation_type = (citation.citation_type or "").strip().lower()
    if citation_type in {"book", "collection"}:
        return CanonicalEntityType.COLLECTION
    if citation_type in {"poet", "author"}:
        return CanonicalEntityType.AUTHOR
    return None
