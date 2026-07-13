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


class ProvenanceRecord(BaseModel):
    """Trace a claim back to the lecture evidence that produced it."""

    chapter_number: int
    source_stage: str
    start: float | None = None
    end: float | None = None
    excerpt: str | None = None
    detector: str | None = None
    prompt_version: str | None = None


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


class ChapterKnowledgeDraft(BaseModel):
    """Structured knowledge output for one lecture chapter."""

    chapter_number: int
    review_status: KnowledgeReviewStatus = KnowledgeReviewStatus.PENDING_EXTRACTION
    source_cleaned_path: Path
    source_annotation_path: Path | None = None
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
