"""Structured poem pilot dataset models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from maana_ingest.ontology.models import CanonicalEntityType, CanonicalResolution


class PoemVerse(BaseModel):
    """Smallest text unit provided by the poem source dataset."""

    unit_number: int
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("verse text must not be empty")
        return text


class PoemTranslation(BaseModel):
    """Optional poem translation record."""

    translation_type: str
    language: str
    translator: str | None = None
    text: str


class PoemOntologyInput(BaseModel):
    """Ontology tags supplied for resolution in the pilot dataset."""

    themes: list[str] = Field(default_factory=list)
    human_experiences: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)


class PoemSourceRecord(BaseModel):
    """One poem entry inside the pilot dataset."""

    poem_id: str
    title: str = ""
    author: str
    collection: str
    source_language: str
    form: str
    literary_unit: str
    source_edition: str
    verses: list[PoemVerse] = Field(default_factory=list)
    translations: list[PoemTranslation] = Field(default_factory=list)
    commentary_references: list[str] = Field(default_factory=list)
    ontology: PoemOntologyInput = Field(default_factory=PoemOntologyInput)

    @field_validator("poem_id", "author", "collection", "source_language", "form", "literary_unit")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("field must not be empty")
        return text


class PoemPilotDataset(BaseModel):
    """Dataset used for the first real-poem ontology pilot."""

    dataset_name: str
    source_edition: str
    poems: list[PoemSourceRecord] = Field(default_factory=list)

    @field_validator("dataset_name", "source_edition")
    @classmethod
    def validate_dataset_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("field must not be empty")
        return text


class ResolvedOntologyTags(BaseModel):
    """Resolved ontology tag groups for a single poem."""

    themes: list[CanonicalResolution] = Field(default_factory=list)
    human_experiences: list[CanonicalResolution] = Field(default_factory=list)
    symbols: list[CanonicalResolution] = Field(default_factory=list)
    concepts: list[CanonicalResolution] = Field(default_factory=list)


class ResolvedPoemRecord(BaseModel):
    """Canonical resolution result for a single poem."""

    poem_id: str
    title: str = ""
    author: CanonicalResolution
    collection: CanonicalResolution
    source_language: CanonicalResolution
    form: CanonicalResolution
    literary_unit: CanonicalResolution
    ontology: ResolvedOntologyTags
    total_resolutions: int
    matched_resolutions: int
    proposed_new_resolutions: int


class PoemResolutionDataset(BaseModel):
    """Persisted output of resolving a poem pilot dataset."""

    dataset_name: str
    source_edition: str
    input_path: Path
    output_path: Path
    total_poems: int
    total_resolutions: int
    matched_resolutions: int
    proposed_new_resolutions: int
    poems: list[ResolvedPoemRecord] = Field(default_factory=list)


class PoemResolutionResult(BaseModel):
    """CLI-facing summary for a resolved poem pilot dataset."""

    dataset_name: str
    input_path: Path
    output_path: Path
    total_poems: int
    total_resolutions: int
    matched_resolutions: int
    proposed_new_resolutions: int


class CuratorDecision(StrEnum):
    """Curator decisions for unresolved ontology candidates."""

    PENDING = "pending"
    CREATE_NEW = "create_new"
    APPROVE_EXISTING = "approve_existing"
    REJECT = "reject"


class ReviewOccurrence(BaseModel):
    """One location where a proposed label appeared in the dataset."""

    poem_id: str
    title: str = ""
    field_path: str
    submitted_label: str


class ReviewCandidate(BaseModel):
    """Deduplicated unresolved label awaiting curator action."""

    entity_type: CanonicalEntityType
    submitted_label: str
    normalized_label: str
    suggested_canonical_id: str
    decision: CuratorDecision = CuratorDecision.PENDING
    existing_canonical_id: str | None = None
    approved_label: str | None = None
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    notes: str | None = None
    occurrences: list[ReviewOccurrence] = Field(default_factory=list)


class PoemReviewFile(BaseModel):
    """Curator review file generated from unresolved resolution results."""

    dataset_name: str
    source_edition: str
    resolved_dataset_path: Path
    review_path: Path
    total_candidates: int
    pending_candidates: int
    candidates: list[ReviewCandidate] = Field(default_factory=list)


class ReviewAppendResult(BaseModel):
    """CLI-facing summary after applying review decisions to the registry."""

    review_path: Path
    registry_path: Path
    applied_path: Path
    appended_entries: int
    skipped_existing: int
    approved_existing: int
    pending_or_rejected: int


class AppliedReviewDecision(BaseModel):
    """Persisted outcome for one curator-reviewed candidate."""

    entity_type: CanonicalEntityType
    submitted_label: str
    decision: CuratorDecision
    resulting_canonical_id: str | None = None
    status: str
    notes: str | None = None


class AppliedReviewFile(BaseModel):
    """Audit file produced after applying a poem review."""

    dataset_name: str
    source_edition: str
    review_path: Path
    registry_path: Path
    applied_path: Path
    appended_entries: int
    skipped_existing: int
    approved_existing: int
    pending_or_rejected: int
    decisions: list[AppliedReviewDecision] = Field(default_factory=list)


class ReviewedResolution(BaseModel):
    """Final reviewed ontology reference after curator decisions are applied."""

    entity_type: CanonicalEntityType
    submitted_label: str
    normalized_label: str
    review_status: str
    canonical_id: str | None = None
    canonical_label: str | None = None


class ReviewedOntologyTags(BaseModel):
    """Final reviewed ontology tags for a poem."""

    themes: list[ReviewedResolution] = Field(default_factory=list)
    human_experiences: list[ReviewedResolution] = Field(default_factory=list)
    symbols: list[ReviewedResolution] = Field(default_factory=list)
    concepts: list[ReviewedResolution] = Field(default_factory=list)


class ReviewedPoemRecord(BaseModel):
    """Curator-reviewed final poem record for downstream ingestion."""

    poem_id: str
    title: str = ""
    author: ReviewedResolution
    collection: ReviewedResolution
    source_language: ReviewedResolution
    form: ReviewedResolution
    literary_unit: ReviewedResolution
    ontology: ReviewedOntologyTags
    fully_reviewed: bool


class ReviewedPoemDataset(BaseModel):
    """Materialized final dataset produced from resolved and reviewed poem artifacts."""

    dataset_name: str
    source_edition: str
    resolved_dataset_path: Path
    applied_review_path: Path
    output_path: Path
    total_poems: int
    fully_reviewed_poems: int
    poems: list[ReviewedPoemRecord] = Field(default_factory=list)


class ReviewedPoemResult(BaseModel):
    """CLI-facing summary for the materialized reviewed poem dataset."""

    dataset_name: str
    output_path: Path
    total_poems: int
    fully_reviewed_poems: int
