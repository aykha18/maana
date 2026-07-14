"""Compose commentary artifacts from approved governed claims."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.config import Settings
from maana_ingest.ontology.commentary_models import (
    ChapterCommentaryArtifact,
    CommentaryClaimRef,
    CommentaryEvidenceRef,
    CommentaryHeader,
    CommentaryOptionalSection,
    CoreExplanationBlock,
    EvidencePostureBlock,
    LectureCommentaryResult,
    OntologyLinksBlock,
    ProvenanceBlock,
    SourceReferenceBlock,
    StatusAndDisagreementBlock,
)
from maana_ingest.ontology.models import ContributorKind, EditorialState, KnowledgeManifest, TruthStatus


class LectureCommentaryError(RuntimeError):
    """Raised when commentary composition cannot proceed."""


class LectureCommentaryComposer:
    """Produce per-chapter commentary artifacts from approved claim bundles."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def compose_from_manifest(
        self,
        knowledge_manifest_path: Path,
        *,
        force: bool = False,
    ) -> LectureCommentaryResult:
        manifest_path = knowledge_manifest_path.expanduser().resolve()
        if not manifest_path.exists():
            raise LectureCommentaryError(f"Knowledge manifest not found: {manifest_path}")

        manifest = self._load_manifest(manifest_path)
        composed = 0
        skipped = 0
        chapter_artifacts: list[Path] = []

        for chapter in manifest.chapters:
            if chapter.claim_bundle_path is None:
                continue
            claim_bundle_path = chapter.claim_bundle_path.expanduser().resolve()
            if not claim_bundle_path.exists():
                raise LectureCommentaryError(f"Claim bundle not found: {claim_bundle_path}")

            chapter_dir = claim_bundle_path.parent
            output_json_path = chapter_dir / "commentary.json"
            output_markdown_path = chapter_dir / "commentary.md"
            if not force and output_json_path.exists() and output_markdown_path.exists():
                skipped += 1
                chapter_artifacts.append(output_json_path)
                continue

            bundle = self._load_claim_bundle(claim_bundle_path)
            approved_claims = [
                claim for claim in bundle.claims if claim.review.editorial_state is EditorialState.APPROVED
            ]
            if not approved_claims:
                skipped += 1
                continue

            claim_refs: list[CommentaryClaimRef] = []
            canonical_ids: set[str] = set()
            textual_anchors: list[CommentaryEvidenceRef] = []
            contributor_classes: set[str] = set()
            methods: set[str] = set()
            source_stages: set[str] = set()
            reviewers: set[str] = set()
            claim_postures: set[str] = set()
            truth_statuses: set[str] = set()
            has_ai_generated_content = False
            has_contested_claims = False

            for claim in approved_claims:
                claim_canonical_ids = sorted(
                    {
                        candidate.canonical_id
                        for candidate in claim.ontology_candidates
                        if candidate.canonical_id
                    }
                )
                canonical_ids.update(claim_canonical_ids)
                evidence_refs = [
                    CommentaryEvidenceRef(
                        start=item.start,
                        end=item.end,
                        excerpt=item.excerpt,
                        source_path=item.source_path,
                    )
                    for item in claim.evidence
                    if item.excerpt or item.start is not None or item.end is not None
                ]
                textual_anchors.extend(evidence_refs)
                claim_postures.add(claim.evidence_posture.value)
                truth_statuses.add(claim.review.truth_status.value)
                if claim.review.truth_status in {TruthStatus.CONTESTED, TruthStatus.DISPUTED}:
                    has_contested_claims = True
                if claim.review.reviewed_by:
                    reviewers.add(claim.review.reviewed_by)
                source_stages.add(claim.source_stage)
                for item in claim.provenance:
                    contributor_classes.add(item.contributor_kind.value)
                    if item.method:
                        methods.add(item.method)
                    if item.source_stage:
                        source_stages.add(item.source_stage)
                    if item.contributor_kind is ContributorKind.AI_SYSTEM:
                        has_ai_generated_content = True
                claim_refs.append(
                    CommentaryClaimRef(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        claim_type=claim.claim_type.value,
                        source_stage=claim.source_stage,
                        evidence_posture=claim.evidence_posture.value,
                        truth_status=claim.review.truth_status.value,
                        ontology_canonical_ids=claim_canonical_ids,
                        evidence=evidence_refs,
                    )
                )

            summary = _build_summary(claim_refs)
            artifact = ChapterCommentaryArtifact(
                lecture_root=manifest.lecture_root,
                chapter_number=chapter.chapter_number,
                output_json_path=output_json_path,
                output_markdown_path=output_markdown_path,
                header=CommentaryHeader(
                    commentary_id=f"chapter-commentary:{chapter.chapter_number:03d}",
                    commentary_type="canonical_commentary",
                    scope_kind="lecture_chapter",
                    scope_reference=f"lecture-chapter:{chapter.chapter_number:03d}",
                    contributor_classes=sorted(contributor_classes) or [ContributorKind.AI_SYSTEM.value],
                    editorial_state="approved",
                    approval_scope="editorial",
                ),
                source_references=SourceReferenceBlock(
                    source_cleaned_path=chapter.source_cleaned_path,
                    source_claim_bundle_path=claim_bundle_path,
                    cited_unit_refs=[f"lecture-chapter:{chapter.chapter_number:03d}"],
                    textual_anchors=_dedupe_evidence(textual_anchors),
                ),
                core_explanation=CoreExplanationBlock(
                    summary=summary,
                    claim_count=len(claim_refs),
                    claims=claim_refs,
                ),
                optional_sections=_build_optional_sections(claim_refs),
                evidence_posture=EvidencePostureBlock(
                    overall_evidence_posture=_overall_evidence_posture(claim_refs),
                    claim_postures=sorted(claim_postures),
                ),
                provenance=ProvenanceBlock(
                    contributor_classes=sorted(contributor_classes) or [ContributorKind.AI_SYSTEM.value],
                    methods=sorted(methods),
                    source_stages=sorted(source_stages),
                    reviewers=sorted(reviewers),
                    ai_involvement=has_ai_generated_content,
                ),
                ontology_links=OntologyLinksBlock(canonical_ontology_ids=sorted(canonical_ids)),
                status_and_disagreement=StatusAndDisagreementBlock(
                    editorial_state="approved",
                    truth_statuses=sorted(truth_statuses),
                    has_contested_claims=has_contested_claims,
                    has_ai_generated_content=has_ai_generated_content,
                    notes=[],
                ),
            )
            output_json_path.write_text(
                json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            output_markdown_path.write_text(
                self._render_markdown(artifact),
                encoding="utf-8",
            )
            composed += 1
            chapter_artifacts.append(output_json_path)

        return LectureCommentaryResult(
            lecture_root=manifest.lecture_root,
            knowledge_manifest_path=manifest_path,
            composed_chapters=composed,
            skipped_chapters=skipped,
            chapter_artifacts=chapter_artifacts,
        )

    @staticmethod
    def _load_manifest(path: Path) -> KnowledgeManifest:
        try:
            return KnowledgeManifest.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise LectureCommentaryError(f"Knowledge manifest is invalid: {path}") from exc

    @staticmethod
    def _load_claim_bundle(path: Path):  # type: ignore[no-untyped-def]
        from maana_ingest.ontology.models import ChapterClaimBundle

        try:
            return ChapterClaimBundle.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise LectureCommentaryError(f"Claim bundle is invalid: {path}") from exc

    @staticmethod
    def _render_markdown(artifact: ChapterCommentaryArtifact) -> str:
        lines = [
            f"# Chapter {artifact.chapter_number} Commentary",
            "",
            "## Commentary Header",
            "",
            f"- Commentary ID: {artifact.header.commentary_id}",
            f"- Type: {artifact.header.commentary_type}",
            f"- Scope: {artifact.header.scope_kind} / {artifact.header.scope_reference}",
            f"- Contributor classes: {', '.join(artifact.header.contributor_classes)}",
            f"- Editorial state: {artifact.header.editorial_state}",
            "",
            "## Source Reference Block",
            "",
            f"- Cleaned source: {artifact.source_references.source_cleaned_path}",
            f"- Claim bundle: {artifact.source_references.source_claim_bundle_path}",
            f"- Unit refs: {', '.join(artifact.source_references.cited_unit_refs)}",
            "",
        ]
        if artifact.source_references.textual_anchors:
            lines.append("- Textual anchors:")
            for item in artifact.source_references.textual_anchors:
                parts = []
                if item.start is not None and item.end is not None:
                    parts.append(f"{item.start:.2f}-{item.end:.2f}")
                if item.excerpt:
                    parts.append(item.excerpt)
                if item.source_path:
                    parts.append(str(item.source_path))
                lines.append(f"  - {' | '.join(parts)}")
            lines.append("")

        lines.extend(
            [
                "## Core Explanation Block",
                "",
                artifact.core_explanation.summary,
                "",
                f"- Claim count: {artifact.core_explanation.claim_count}",
                "",
            ]
        )
        if artifact.ontology_links.canonical_ontology_ids:
            lines.append("## Ontology Links")
            lines.append("")
            for canonical_id in artifact.ontology_links.canonical_ontology_ids:
                lines.append(f"- {canonical_id}")
            lines.append("")

        if artifact.optional_sections:
            lines.append("## Optional Commentary Sections")
            lines.append("")
            for section in artifact.optional_sections:
                lines.append(f"### {section.title}")
                lines.append("")
                lines.append(section.summary)
                lines.append("")
                lines.append(f"- Claim count: {section.claim_count}")
                for claim in section.claims:
                    lines.append(f"- {claim.claim_id}: {claim.statement}")
                lines.append("")

        lines.append("## Approved Claims")
        lines.append("")
        for claim in artifact.core_explanation.claims:
            lines.append(f"### {claim.claim_id}")
            lines.append("")
            lines.append(f"- Type: {claim.claim_type}")
            lines.append(f"- Stage: {claim.source_stage}")
            lines.append(f"- Evidence posture: {claim.evidence_posture}")
            lines.append(f"- Truth status: {claim.truth_status}")
            lines.append(f"- Statement: {claim.statement}")
            if claim.ontology_canonical_ids:
                lines.append("- Ontology:")
                for canonical_id in claim.ontology_canonical_ids:
                    lines.append(f"  - {canonical_id}")
            if claim.evidence:
                lines.append("- Evidence:")
                for item in claim.evidence:
                    span = []
                    if item.start is not None and item.end is not None:
                        span.append(f"{item.start:.2f}-{item.end:.2f}")
                    if item.excerpt:
                        span.append(item.excerpt)
                    if item.source_path:
                        span.append(str(item.source_path))
                    lines.append(f"  - {' | '.join(span) if span else 'evidence'}")
            lines.append("")

        lines.extend(
            [
                "## Evidence Or Evidence Posture Block",
                "",
                f"- Overall evidence posture: {artifact.evidence_posture.overall_evidence_posture}",
                f"- Claim postures: {', '.join(artifact.evidence_posture.claim_postures)}",
                "",
                "## Provenance Block",
                "",
                f"- Contributor classes: {', '.join(artifact.provenance.contributor_classes)}",
                f"- Methods: {', '.join(artifact.provenance.methods) if artifact.provenance.methods else 'n/a'}",
                f"- Source stages: {', '.join(artifact.provenance.source_stages)}",
                f"- Reviewers: {', '.join(artifact.provenance.reviewers) if artifact.provenance.reviewers else 'n/a'}",
                f"- AI involvement: {artifact.provenance.ai_involvement}",
                "",
                "## Status And Disagreement Block",
                "",
                f"- Editorial state: {artifact.status_and_disagreement.editorial_state}",
                f"- Truth statuses: {', '.join(artifact.status_and_disagreement.truth_statuses)}",
                f"- Has contested claims: {artifact.status_and_disagreement.has_contested_claims}",
                f"- Has AI-generated content: {artifact.status_and_disagreement.has_ai_generated_content}",
                "",
            ]
        )

        return "\n".join(lines).rstrip() + "\n"


def _build_summary(claims: list[CommentaryClaimRef]) -> str:
    if not claims:
        return "No approved commentary claims are available."
    statements = [claim.statement.strip() for claim in claims if claim.statement.strip()]
    if not statements:
        return "Approved claims exist, but no summary statements are available."
    return " ".join(statements[:2])


def _build_optional_sections(claims: list[CommentaryClaimRef]) -> list[CommentaryOptionalSection]:
    section_specs = [
        ("literal_clarification", "Literal Clarification", {"textual"}),
        ("descriptive_reading", "Descriptive Reading", {"descriptive", "ontological"}),
        ("interpretive_reading", "Interpretive Reading", {"interpretive"}),
        ("comparative_references", "Comparative References", {"referential", "relational"}),
        ("historical_context", "Historical Context", {"historical"}),
        ("synthetic_reflection", "Synthetic Reflection", {"inferential"}),
    ]
    sections: list[CommentaryOptionalSection] = []
    for key, title, supported_types in section_specs:
        section_claims = [claim for claim in claims if claim.claim_type in supported_types]
        if not section_claims:
            continue
        sections.append(
            CommentaryOptionalSection(
                section_key=key,
                title=title,
                summary=_summarize_section(section_claims),
                claim_count=len(section_claims),
                claims=section_claims,
            )
        )
    return sections


def _summarize_section(claims: list[CommentaryClaimRef]) -> str:
    statements = [claim.statement.strip() for claim in claims if claim.statement.strip()]
    if not statements:
        return "Approved claims are available for this section."
    return " ".join(statements[:2])


def _overall_evidence_posture(claims: list[CommentaryClaimRef]) -> str:
    postures = {claim.evidence_posture for claim in claims}
    if "directly_evidenced" in postures:
        return "directly_evidenced"
    if "strongly_supported" in postures:
        return "strongly_supported"
    if "plausibly_supported" in postures:
        return "plausibly_supported"
    return sorted(postures)[0] if postures else "unsupported"


def _dedupe_evidence(items: list[CommentaryEvidenceRef]) -> list[CommentaryEvidenceRef]:
    seen: set[tuple[float | None, float | None, str | None, str | None]] = set()
    unique: list[CommentaryEvidenceRef] = []
    for item in items:
        key = (
            item.start,
            item.end,
            item.excerpt,
            str(item.source_path) if item.source_path is not None else None,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
