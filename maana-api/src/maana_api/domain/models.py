"""Core domain models for Ma'na semantic infrastructure."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Column, JSON, Text
from sqlmodel import SQLModel, Field as SQLField


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

class Scope(StrEnum):
    """Governance scope for knowledge objects."""

    GLOBAL = "global"
    TRADITION = "tradition"
    WORKSPACE = "workspace"


# ---------------------------------------------------------------------------
# World Lifecycle
# ---------------------------------------------------------------------------

class WorldStatus(StrEnum):
    """Lifecycle states for a World."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    MERGED = "merged"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Claim Lifecycle
# ---------------------------------------------------------------------------

class ClaimStatus(StrEnum):
    """Lifecycle states for a Claim."""

    DISCOVERED = "discovered"
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    CHALLENGED = "challenged"


# ---------------------------------------------------------------------------
# Claim Types
# ---------------------------------------------------------------------------

class ClaimType(StrEnum):
    """High-level governed claim classes."""

    FACTUAL = "factual"
    DESCRIPTIVE = "descriptive"
    INTERPRETIVE = "interpretive"
    COMPARATIVE = "comparative"
    HISTORICAL = "historical"
    ONTOLOGICAL = "ontological"
    RELATIONAL = "relational"
    EDITORIAL = "editorial"
    INFERENTIAL = "inferential"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceDimension(StrEnum):
    """Multidimensional evidence strength factors."""

    SOURCE_AUTHORITY = "source_authority"
    DIRECTNESS = "directness"
    TEXTUAL_PROXIMITY = "textual_proximity"
    SCHOLARLY_RELIABILITY = "scholarly_reliability"
    INDEPENDENCE = "independence"
    SPECIFICITY = "specificity"
    VERIFICATION_STATUS = "verification_status"


class EvidenceType(StrEnum):
    """Evidence families attached to governed claims."""

    TEXT_SPAN = "text_span"
    CITATION = "citation"
    MANUSCRIPT = "manuscript"
    COMMENTARY = "commentary"
    COMPARATIVE_PASSAGE = "comparative_passage"
    LEXICAL = "lexical"
    AI_EXTRACTION = "ai_extraction"


class Evidence(BaseModel):
    """Any support, constraint, or challenge for a claim."""

    evidence_id: str
    evidence_type: EvidenceType
    source_ref: str
    text: str | None = None
    start: float | None = None
    end: float | None = None
    dimensions: dict[EvidenceDimension, float] = SQLField(default_factory=dict)
    notes: str | None = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

class ContributorKind(StrEnum):
    """Who produced or materially shaped a governed knowledge object."""

    EDITOR = "editor"
    SCHOLAR = "scholar"
    CURATOR = "curator"
    TRANSLATOR = "translator"
    READER = "reader"
    AI_SYSTEM = "ai_system"
    PIPELINE = "pipeline"
    SYSTEM = "system"


class ProvenanceRecord(BaseModel):
    """The record of where a claim came from."""

    contributor_kind: ContributorKind
    contributor_id: str | None = None
    source: str | None = None
    method: str | None = None
    timestamp: datetime = SQLField(default_factory=datetime.utcnow)
    process: str | None = None
    model: str | None = None
    tool: str | None = None
    review_history: list[str] = SQLField(default_factory=list)


# ---------------------------------------------------------------------------
# Source / Witness / Segment / Unit
# ---------------------------------------------------------------------------

class Source(BaseModel):
    """Any preserved input artifact from which Ma'na derives knowledge."""

    source_id: str
    source_type: str
    uri: str
    title: str | None = None
    description: str | None = None
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class Witness(BaseModel):
    """A specific textual or transmitted instance of a work."""

    witness_id: str
    work_id: str
    witness_type: str
    label: str
    description: str | None = None
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


class Segment(BaseModel):
    """Any addressable span inside a witness or source."""

    segment_id: str
    witness_id: str
    segment_type: str
    start: float | None = None
    end: float | None = None
    text: str | None = None
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


class Unit(BaseModel):
    """A segment that has been editorially recognized as a meaning-bearing interpretive boundary."""

    unit_id: str
    segment_id: str
    work_id: str
    unit_type: str
    label: str | None = None
    interpretation: str | None = None
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


# ---------------------------------------------------------------------------
# Chapter / Part / SemanticCluster
# ---------------------------------------------------------------------------

class Chapter(BaseModel):
    """A major semantic section."""

    chapter_id: str
    title: str
    title_transliteration: str | None = None
    description: str | None = None
    central_question: str | None = None
    order: int
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


class Part(BaseModel):
    """A subdivision of a Chapter."""

    part_id: str
    chapter_id: str
    title: str
    description: str | None = None
    order: int
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


class SemanticCluster(BaseModel):
    """A finer grouping within a Part. First-class graph node."""

    cluster_id: str
    chapter_id: str
    part_id: str | None = None
    title: str
    description: str | None = None
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class World(SQLModel, table=True):
    """A semantic concept with multilingual identity."""

    world_id: str = SQLField(primary_key=True, index=True)
    canonical_term: str = SQLField(index=True)
    transliteration: str | None = None
    persian_term: str | None = None
    urdu_term: str | None = None
    arabic_root: str | None = None
    english_gloss: str | None = None
    short_definition: str | None = None
    literal_meaning: str | None = None
    expanded_meaning: str | None = None
    central_question: str | None = None
    central_axis: str | None = None
    semantic_dimensions: dict[str, str] = SQLField(default={}, sa_column=Column(JSON))
    status: WorldStatus = SQLField(default=WorldStatus.PROPOSED, index=True)
    scope: Scope = SQLField(default=Scope.GLOBAL, index=True)
    chapter_id: str | None = SQLField(default=None, index=True)
    cluster_id: str | None = SQLField(default=None, index=True)
    current_version_id: str | None = None
    version_history: list[str] = SQLField(default=[], sa_column=Column(JSON))
    provenance: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# LexicalForm / WordFamily
# ---------------------------------------------------------------------------

class LexicalForm(BaseModel):
    """A word or phrase in a specific language. Not the same as a World."""

    lexical_id: str
    term: str
    language: str
    transliteration: str | None = None
    root: str | None = None
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


class WordFamily(BaseModel):
    """A linguistic grouping of related lexical forms."""

    family_id: str
    root: str
    language: str
    members: list[str] = SQLField(default_factory=list)
    extra_metadata: dict[str, Any] = SQLField(default_factory=dict)


# ---------------------------------------------------------------------------
# Relation
# ---------------------------------------------------------------------------

class RelationType(StrEnum):
    """Semantic relationship taxonomy."""

    PART_OF = "part_of"
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    RELATED_TO = "related_to"
    CONTRASTS_WITH = "contrasts_with"
    OPPOSITE_OF = "opposite_of"
    DEEPENS = "deepens"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    EXPANDS = "expands"
    WORD_FAMILY = "word_family"
    DERIVED_FROM = "derived_from"
    SYNONYM_OF = "synonym_of"
    NEAR_SYNONYM_OF = "near_synonym_of"
    ANTONYM_OF = "antonym_of"
    USED_BY = "used_by"
    DEVELOPED_BY = "developed_by"
    SYMBOLIZED_BY = "symbolized_by"
    THEME_OF = "theme_of"
    SEMANTIC_BRIDGE = "semantic_bridge"
    RING_LINK = "ring_link"
    CHAPTER_ANCHOR = "chapter_anchor"
    CLUSTER_ANCHOR = "cluster_anchor"
    TRANSITION_TO = "transition_to"


class Relation(SQLModel, table=True):
    """A meaning-bearing connection between two Worlds. A governed knowledge assertion."""

    relation_id: str = SQLField(primary_key=True, index=True)
    relation_type: str = SQLField(index=True)
    source_world_id: str = SQLField(foreign_key="world.world_id", index=True)
    target_world_id: str = SQLField(foreign_key="world.world_id", index=True)
    claim_id: str | None = None
    status: WorldStatus = SQLField(default=WorldStatus.PROPOSED, index=True)
    scope: Scope = SQLField(default=Scope.GLOBAL, index=True)
    provenance: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# SemanticPath
# ---------------------------------------------------------------------------

class SemanticPath(SQLModel, table=True):
    """A first-class entity representing a meaningful journey through Worlds."""

    path_id: str = SQLField(primary_key=True, index=True)
    title: str
    description: str | None = None
    world_ids: list[str] = SQLField(default=[], sa_column=Column(JSON))
    scope: Scope = SQLField(default=Scope.GLOBAL, index=True)
    provenance: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------

class SubjectRef(SQLModel):
    """Addressable subject reference for a governed claim."""

    kind: str
    reference_id: str
    label: str | None = None


class Claim(SQLModel, table=True):
    """The smallest active knowledge object in Ma'na. One assertion per claim."""

    claim_id: str = SQLField(primary_key=True, index=True)
    claim_type: str = SQLField(index=True)
    subject_kind: str
    subject_reference_id: str = SQLField(index=True)
    subject_label: str | None = None
    predicate: str = SQLField(index=True)
    object: str | None = None
    text: str = SQLField(sa_column=Column(Text))
    status: str = SQLField(default="proposed", index=True)
    scope: str = SQLField(default="global", index=True)
    confidence: float = SQLField(default=0.0)
    evidence: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    provenance: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# OntologyRegistry
# ---------------------------------------------------------------------------

class OntologyRegistryEntry(SQLModel, table=True):
    """Canonical World entry with aliases and translations."""

    world_id: str = SQLField(primary_key=True, index=True)
    canonical_term: str = SQLField(index=True)
    aliases: list[str] = SQLField(default=[], sa_column=Column(JSON))
    translations: dict[str, str] = SQLField(default={}, sa_column=Column(JSON))
    spellings: list[str] = SQLField(default=[], sa_column=Column(JSON))
    historical_forms: list[str] = SQLField(default=[], sa_column=Column(JSON))
    language_forms: dict[str, str] = SQLField(default={}, sa_column=Column(JSON))
    status: str = SQLField(default="approved", index=True)
    extra_metadata: dict[str, Any] = SQLField(default={}, sa_column=Column(JSON))


# ---------------------------------------------------------------------------
# Embedding Provenance
# ---------------------------------------------------------------------------

class EmbeddingProvenance(SQLModel, table=True):
    """Provenance record for an embedding."""

    embedding_id: str = SQLField(primary_key=True, index=True)
    entity_id: str = SQLField(index=True)
    entity_type: str = SQLField(index=True)
    embedding_type: str = SQLField(index=True)
    model: str
    model_version: str
    dimensions: int
    source_version: str | None = None
    content_hash: str | None = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Embedding (pgvector)
# ---------------------------------------------------------------------------

class Embedding(SQLModel, table=True):
    """Vector embedding with pgvector."""

    __tablename__ = "embeddings"

    embedding_id: str = SQLField(primary_key=True, index=True)
    entity_id: str = SQLField(index=True)
    entity_type: str = SQLField(index=True)
    embedding_type: str = SQLField(index=True)
    model: str
    model_version: str
    dimensions: int
    vector: list[float] = SQLField(sa_column=Column("vector", JSON))  # pgvector stores as vector type
    source_version: str | None = None
    content_hash: str | None = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


