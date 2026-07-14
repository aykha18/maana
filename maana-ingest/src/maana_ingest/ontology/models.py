"""Ontology and knowledge-extraction contracts for Phase 6 foundations."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class CanonicalEntityType(StrEnum):
    """Language-independent entity families defined by the architecture vision."""

    CIVILIZATION = "civilization"
    LANGUAGE = "language"
    AUTHOR = "author"
    COLLECTION = "collection"
    LITERARY_WORK = "literary_work"
    LITERARY_UNIT = "literary_unit"
    VOCABULARY = "vocabulary"
    THEME = "theme"
    HUMAN_EXPERIENCE = "human_experience"
    SYMBOL = "symbol"
    CONCEPT = "concept"
    LITERARY_DEVICE = "literary_device"
    COMMENTARY = "commentary"


class CanonicalMappingStatus(StrEnum):
    """Mapping outcome for a proposed knowledge object."""

    MATCHED = "matched"
    PROPOSED_NEW = "proposed_new"
    UNRESOLVED = "unresolved"


class KnowledgeReviewStatus(StrEnum):
    """Review state before an object becomes canonical."""

    PENDING_EXTRACTION = "pending_extraction"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ContributorKind(StrEnum):
    """Who produced or materially shaped a governed knowledge object."""

    SCHOLAR = "scholar"
    EDITOR = "editor"
    CURATOR = "curator"
    TRANSLATOR = "translator"
    READER = "reader"
    AI_SYSTEM = "ai_system"
    PIPELINE = "pipeline"
    SYSTEM = "system"


class ClaimType(StrEnum):
    """High-level governed claim classes."""

    TEXTUAL = "textual"
    DESCRIPTIVE = "descriptive"
    INTERPRETIVE = "interpretive"
    REFERENTIAL = "referential"
    ONTOLOGICAL = "ontological"
    RELATIONAL = "relational"
    HISTORICAL = "historical"
    EDITORIAL = "editorial"
    INFERENTIAL = "inferential"


class EvidenceType(StrEnum):
    """Evidence families attached to governed claims."""

    TEXT_SPAN = "text_span"
    CLEANED_TRANSCRIPT_SEGMENT = "cleaned_transcript_segment"
    ANNOTATION_HIT = "annotation_hit"
    CITATION = "citation"
    STRUCTURED_ARTIFACT = "structured_artifact"


class EvidencePosture(StrEnum):
    """Strength posture for a claim's evidentiary grounding."""

    DIRECTLY_EVIDENCED = "directly_evidenced"
    STRONGLY_SUPPORTED = "strongly_supported"
    PLAUSIBLY_SUPPORTED = "plausibly_supported"
    TRADITION_BACKED = "tradition_backed"
    INFERENTIAL = "inferential"
    SPECULATIVE = "speculative"
    UNSUPPORTED = "unsupported"


class EditorialState(StrEnum):
    """Workflow state for governed objects."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    IN_REVIEW = "in_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    CONTESTED = "contested"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class TruthStatus(StrEnum):
    """Epistemic standing of a governed claim."""

    VERIFIED = "verified"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    DISPUTED = "disputed"
    UNRESOLVED = "unresolved"
    SPECULATIVE = "speculative"
    INFERRED = "inferred"
    DEPRECATED = "deprecated"


class ApprovalScope(StrEnum):
    """Scope within which a governed object may be approved."""

    PRIVATE = "private"
    EDITORIAL = "editorial"
    WORK = "work"
    WITNESS = "witness"
    UNIT = "unit"
    TRADITION = "tradition"
    LANGUAGE = "language"
    HOUSE = "house"
    GLOBAL = "global"


class CuratorClaimDecision(StrEnum):
    """Curator action for a governed claim review item."""

    PENDING = "pending"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"


class CuratorOntologyDecision(StrEnum):
    """Curator action for an ontology candidate nested under a claim."""

    PENDING = "pending"
    APPROVE_EXISTING = "approve_existing"
    CREATE_NEW = "create_new"
    REJECT = "reject"


class ClaimSubjectKind(StrEnum):
    """Addressable targets for governed claims."""

    LECTURE_CHAPTER = "lecture_chapter"
    UNIT = "unit"
    WORK = "work"
    WITNESS = "witness"
    QUESTION = "question"
    ONTOLOGY_ENTITY = "ontology_entity"


class ProvenanceRecord(BaseModel):
    """Trace a claim back to the lecture evidence that produced it."""

    chapter_number: int
    source_stage: str
    start: float | None = None
    end: float | None = None
    excerpt: str | None = None
    detector: str | None = None
    prompt_version: str | None = None
    contributor_kind: ContributorKind = ContributorKind.PIPELINE
    contributor_id: str | None = None
    method: str | None = None
    model_name: str | None = None
    source_path: Path | None = None


class ClaimSubjectRef(BaseModel):
    """Addressable subject reference for a governed claim."""

    kind: ClaimSubjectKind
    reference_id: str
    label: str | None = None
    source_path: Path | None = None


class ClaimEvidence(BaseModel):
    """Evidence attachment preserved with a governed claim."""

    evidence_type: EvidenceType
    source_stage: str
    source_path: Path | None = None
    analyzer_name: str | None = None
    label: str | None = None
    excerpt: str | None = None
    start: float | None = None
    end: float | None = None
    notes: str | None = None


class ReviewState(BaseModel):
    """Scoped workflow and truth state for a governed object."""

    editorial_state: EditorialState = EditorialState.PROPOSED
    truth_status: TruthStatus = TruthStatus.UNRESOLVED
    approval_scope: ApprovalScope = ApprovalScope.EDITORIAL
    reviewed_by: str | None = None
    notes: str | None = None


class CanonicalEntityCandidate(BaseModel):
    """Proposed ontology entity produced by extraction."""

    entity_type: CanonicalEntityType
    label: str
    normalized_label: str | None = None
    canonical_id: str | None = None
    mapping_status: CanonicalMappingStatus = CanonicalMappingStatus.UNRESOLVED
    confidence: float | None = None
    rationale: str | None = None
    aliases: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)


class CanonicalRegistryEntry(BaseModel):
    """Canonical entity stored in the reusable registry."""

    canonical_id: str
    entity_type: CanonicalEntityType
    label: str
    normalized_label: str | None = None
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)


class CanonicalRegistry(BaseModel):
    """Persistent registry of approved ontology entities."""

    version: str
    entries: list[CanonicalRegistryEntry] = Field(default_factory=list)


class CanonicalResolution(BaseModel):
    """Resolver output for a candidate label against the canonical registry."""

    entity_type: CanonicalEntityType
    submitted_label: str
    normalized_label: str
    mapping_status: CanonicalMappingStatus
    matched_entry: CanonicalRegistryEntry | None = None
    matched_on: str | None = None
    rationale: str | None = None


class VocabularyCandidate(BaseModel):
    """Vocabulary entry extracted from a lecture chapter."""

    word: str
    language: str | None = None
    root: str | None = None
    meaning: str | None = None
    usage: str | None = None
    etymology: str | None = None
    provenance: list[ProvenanceRecord] = Field(default_factory=list)


class CommentaryDraft(BaseModel):
    """First-class commentary draft tied to evidence instead of replacing it."""

    title: str | None = None
    body: str
    provenance: list[ProvenanceRecord] = Field(default_factory=list)


class GovernedClaim(BaseModel):
    """Claim-oriented intermediate object for the governed knowledge layer."""

    claim_id: str
    claim_type: ClaimType
    subject: ClaimSubjectRef
    statement: str
    source_stage: str
    evidence_posture: EvidencePosture = EvidencePosture.PLAUSIBLY_SUPPORTED
    evidence: list[ClaimEvidence] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    review: ReviewState = Field(default_factory=ReviewState)
    ontology_candidates: list[CanonicalEntityCandidate] = Field(default_factory=list)
    originating_analyzers: list[str] = Field(default_factory=list)


class ChapterClaimBundle(BaseModel):
    """Governed claim bundle emitted for one lecture chapter."""

    chapter_number: int
    lecture_root: Path
    bundle_path: Path
    source_cleaned_path: Path
    source_annotation_path: Path | None = None
    generated_from_provider: str | None = None
    generated_from_prompt_version: str | None = None
    claim_count: int = 0
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.PENDING_REVIEW
    claims: list[GovernedClaim] = Field(default_factory=list)


class CuratorOntologyCandidateReview(BaseModel):
    """Reviewable ontology proposal attached to a governed claim."""

    entity_type: CanonicalEntityType
    submitted_label: str
    normalized_label: str | None = None
    current_mapping_status: CanonicalMappingStatus = CanonicalMappingStatus.UNRESOLVED
    suggested_canonical_id: str | None = None
    decision: CuratorOntologyDecision = CuratorOntologyDecision.PENDING
    existing_canonical_id: str | None = None
    approved_label: str | None = None
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    notes: str | None = None


class CuratorClaimReviewItem(BaseModel):
    """One claim queued for curator review."""

    chapter_number: int
    claim_id: str
    claim_type: ClaimType
    statement: str
    source_stage: str
    evidence_posture: EvidencePosture
    current_editorial_state: EditorialState
    current_truth_status: TruthStatus
    approval_scope: ApprovalScope
    decision: CuratorClaimDecision = CuratorClaimDecision.PENDING
    reviewed_truth_status: TruthStatus | None = None
    reviewed_by: str | None = None
    notes: str | None = None
    ontology_reviews: list[CuratorOntologyCandidateReview] = Field(default_factory=list)


class LectureClaimReviewFile(BaseModel):
    """Curator review file generated from lecture claim bundles."""

    lecture_root: Path
    knowledge_manifest_path: Path
    review_path: Path
    total_items: int
    pending_items: int
    items: list[CuratorClaimReviewItem] = Field(default_factory=list)


class AppliedClaimReviewItem(BaseModel):
    """Audit record for one applied claim review decision."""

    chapter_number: int
    claim_id: str
    decision: CuratorClaimDecision
    status: str
    resulting_editorial_state: EditorialState
    resulting_truth_status: TruthStatus
    ontology_results: list[str] = Field(default_factory=list)
    notes: str | None = None


class AppliedLectureClaimReviewFile(BaseModel):
    """Audit file produced after applying lecture claim review decisions."""

    lecture_root: Path
    review_path: Path
    registry_path: Path | None = None
    applied_path: Path
    approved_claims: int
    rejected_claims: int
    revision_requested_claims: int
    pending_claims: int
    ontology_appended_entries: int
    ontology_approved_existing: int
    ontology_rejected: int
    items: list[AppliedClaimReviewItem] = Field(default_factory=list)


class LectureClaimReviewResult(BaseModel):
    """CLI-facing summary for a generated lecture claim review file."""

    lecture_root: Path
    review_path: Path
    total_items: int
    pending_items: int


class ApplyLectureClaimReviewResult(BaseModel):
    """CLI-facing summary after curator review decisions are applied."""

    review_path: Path
    applied_path: Path
    registry_path: Path | None = None
    approved_claims: int
    rejected_claims: int
    revision_requested_claims: int
    pending_claims: int
    ontology_appended_entries: int
    ontology_approved_existing: int
    ontology_rejected: int


class ChapterKnowledgeDraft(BaseModel):
    """Structured knowledge output for one lecture chapter."""

    chapter_number: int
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.PENDING_EXTRACTION
    source_cleaned_path: Path
    source_annotation_path: Path | None = None
    claim_bundle_path: Path | None = None
    claim_count: int = 0
    summary: str | None = None
    detailed_explanation: str | None = None
    vocabulary: list[VocabularyCandidate] = Field(default_factory=list)
    themes: list[CanonicalEntityCandidate] = Field(default_factory=list)
    human_experiences: list[CanonicalEntityCandidate] = Field(default_factory=list)
    symbols: list[CanonicalEntityCandidate] = Field(default_factory=list)
    concepts: list[CanonicalEntityCandidate] = Field(default_factory=list)
    literary_devices: list[CanonicalEntityCandidate] = Field(default_factory=list)
    commentaries: list[CommentaryDraft] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class KnowledgeManifest(BaseModel):
    """Lecture-level knowledge extraction manifest."""

    lecture_root: Path
    knowledge_dir: Path
    manifest_path: Path
    total_chapters: int
    chapters_pending_review: int = 0
    ready_for_canonical_ingestion: bool = False
    blockers: list[str] = Field(default_factory=list)
    chapters: list[ChapterKnowledgeDraft] = Field(default_factory=list)


class ReadinessAssessment(BaseModel):
    """Operational answer to whether a lecture is ready for ingestion stages."""

    lecture_root: Path
    can_start_artifact_ingestion: bool
    can_start_knowledge_ingestion: bool
    curator_ui_ready: bool
    annotation_provider: str
    available_artifacts: dict[str, bool] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    next_tasks: list[str] = Field(default_factory=list)
    summary: str
