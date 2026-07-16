"""Export commentary artifacts to concrete output formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from maana_ingest.ontology.commentary_models import ChapterCommentaryArtifact


class CommentaryArtifactExporter(Protocol):
    """Exporter interface for commentary artifacts."""

    output_path_attr: str

    def export(self, artifact: ChapterCommentaryArtifact) -> Path:
        """Write one artifact representation and return the output path."""


class CommentaryJsonExporter:
    """Write commentary artifacts as canonical JSON."""

    output_path_attr = "output_json_path"

    def export(self, artifact: ChapterCommentaryArtifact) -> Path:
        output_path = artifact.output_json_path
        output_path.write_text(
            json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path


class CommentaryMarkdownExporter:
    """Write commentary artifacts as human-readable Markdown."""

    output_path_attr = "output_markdown_path"

    def export(self, artifact: ChapterCommentaryArtifact) -> Path:
        output_path = artifact.output_markdown_path
        output_path.write_text(render_commentary_markdown(artifact), encoding="utf-8")
        return output_path


class CommentaryExportService:
    """Coordinate exporting commentary artifacts to the configured formats."""

    def __init__(self, exporters: list[CommentaryArtifactExporter] | None = None) -> None:
        self._exporters = exporters or [
            CommentaryJsonExporter(),
            CommentaryMarkdownExporter(),
        ]

    def outputs_exist(self, artifact: ChapterCommentaryArtifact) -> bool:
        """Return whether every configured exporter output already exists."""

        return all(path.exists() for path in self.target_output_paths(artifact))

    def target_output_paths(self, artifact: ChapterCommentaryArtifact) -> list[Path]:
        """Return the output paths implied by the configured exporters."""

        return [getattr(artifact, exporter.output_path_attr) for exporter in self._exporters]

    def export(self, artifact: ChapterCommentaryArtifact) -> list[Path]:
        """Export the artifact through every configured exporter."""

        return [exporter.export(artifact) for exporter in self._exporters]


def render_commentary_markdown(artifact: ChapterCommentaryArtifact) -> str:
    """Render a commentary artifact to Markdown."""

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
        if claim.interpretation_mode:
            lines.append(f"- Interpretation mode: {claim.interpretation_mode}")
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
