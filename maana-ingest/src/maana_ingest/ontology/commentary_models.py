"""Commentary artifact models composed from governed claims."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class CommentaryEvidenceRef(BaseModel):
    start: float | None = None
    end: float | None = None
    excerpt: str | None = None
    source_path: Path | None = None


class CommentaryClaimRef(BaseModel):
    claim_id: str
    statement: str
    claim_type: str
    source_stage: str
    evidence_posture: str
    truth_status: str
    ontology_canonical_ids: list[str] = Field(default_factory=list)
    evidence: list[CommentaryEvidenceRef] = Field(default_factory=list)


class CommentaryHeader(BaseModel):
    commentary_id: str
    commentary_type: str
    scope_kind: str
    scope_reference: str
    language: str = "en"
    contributor_classes: list[str] = Field(default_factory=list)
    editorial_state: str
    approval_scope: str


class SourceReferenceBlock(BaseModel):
    source_cleaned_path: Path
    source_claim_bundle_path: Path
    cited_unit_refs: list[str] = Field(default_factory=list)
    textual_anchors: list[CommentaryEvidenceRef] = Field(default_factory=list)


class CoreExplanationBlock(BaseModel):
    summary: str
    claim_count: int
    claims: list[CommentaryClaimRef] = Field(default_factory=list)


class CommentaryOptionalSection(BaseModel):
    section_key: str
    title: str
    summary: str
    claim_count: int
    claims: list[CommentaryClaimRef] = Field(default_factory=list)


class EvidencePostureBlock(BaseModel):
    overall_evidence_posture: str
    claim_postures: list[str] = Field(default_factory=list)


class ProvenanceBlock(BaseModel):
    contributor_classes: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    source_stages: list[str] = Field(default_factory=list)
    reviewers: list[str] = Field(default_factory=list)
    ai_involvement: bool = False


class OntologyLinksBlock(BaseModel):
    canonical_ontology_ids: list[str] = Field(default_factory=list)


class StatusAndDisagreementBlock(BaseModel):
    editorial_state: str
    truth_statuses: list[str] = Field(default_factory=list)
    has_contested_claims: bool = False
    has_ai_generated_content: bool = False
    notes: list[str] = Field(default_factory=list)


class ChapterCommentaryArtifact(BaseModel):
    lecture_root: Path
    chapter_number: int
    output_json_path: Path
    output_markdown_path: Path
    header: CommentaryHeader
    source_references: SourceReferenceBlock
    core_explanation: CoreExplanationBlock
    optional_sections: list[CommentaryOptionalSection] = Field(default_factory=list)
    evidence_posture: EvidencePostureBlock
    provenance: ProvenanceBlock
    ontology_links: OntologyLinksBlock
    status_and_disagreement: StatusAndDisagreementBlock


class LectureCommentaryResult(BaseModel):
    lecture_root: Path
    knowledge_manifest_path: Path
    composed_chapters: int
    skipped_chapters: int
    chapter_artifacts: list[Path] = Field(default_factory=list)
