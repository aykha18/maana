"""Core domain models for Ma'na semantic infrastructure."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field
from sqlalchemy import CheckConstraint, Column, JSON, Text, TypeDecorator
from sqlmodel import SQLModel, Field as SQLField


# ---------------------------------------------------------------------------
# Dialect-aware embedding vector
# ---------------------------------------------------------------------------

class EmbeddingVector(TypeDecorator):
    """pgvector ``vector`` on PostgreSQL, JSON elsewhere.

    The test suite runs on SQLite, where the native pgvector type is not
    available. Both dialects round-trip a plain ``list[float]``, so application
    code and the domain model never branch on dialect.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 1536, **kwargs: Any) -> None:
        self.dimensions = dimensions
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value)
        return [float(v) for v in value]

    def process_result_value(self, value: Any, dialect) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = [float(part) for part in value.strip("[]").split(",") if part.strip()]
        return [float(v) for v in value]


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
# Challenge Lifecycle
# ---------------------------------------------------------------------------

class ChallengeStatus(StrEnum):
    """Challenge lifecycle states."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"


class ChallengeResolution(StrEnum):
    """How a challenge was resolved."""

    REAFFIRMED = "reaffirmed"      # Original stands, challenge rejected
    SUPERSEDED = "superseded"      # New version created, old superseded
    MERGED = "merged"              # Merged into another entity
    WITHDRAWN = "withdrawn"        # Challenger withdrew


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


class RelationType(StrEnum):
    """Semantic relationship taxonomy (Ontology v1.0 §6.10)."""

    PART_OF = "part_of"
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    RELATED_TO = "related_to"
    CONTRASTS_WITH = "contrasts_with"
    OPPOSITE_OF = "opposite_of"
    DEEPENS = "deepens"
    DEEPENS_TOWARD = "deepens_toward"
    DEEPENS_INTO = "deepens_into"
    DEEPENS_THROUGH = "deepens_through"
    DEEPENS_TO = "deepens_to"
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
    REALIZED_BY = "realized_by"
    MERGED_INTO = "merged_into"


#: Directional relation types and their declared inverses (Ontology v1.0 I-042).
#: Symmetric types map to themselves in meaning but are listed explicitly so
#: that every type is accounted for.
RELATION_INVERSES: dict[str, str] = {
    RelationType.PRECEDES.value: RelationType.FOLLOWS.value,
    RelationType.FOLLOWS.value: RelationType.PRECEDES.value,
    RelationType.DEEPENS.value: "deepened_by",
    RelationType.DEEPENS_TOWARD.value: "deepened_toward_by",
    RelationType.DEEPENS_INTO.value: "deepened_into_by",
    RelationType.DEEPENS_THROUGH.value: "deepened_through_by",
    RelationType.DEEPENS_TO.value: "deepened_to_by",
    RelationType.EXPANDS.value: "expanded_by",
    RelationType.PART_OF.value: RelationType.CONTAINS.value,
    RelationType.CONTAINS.value: RelationType.PART_OF.value,
    RelationType.BELONGS_TO.value: RelationType.CONTAINS.value,
    RelationType.DERIVED_FROM.value: "derives",
    RelationType.WORD_FAMILY.value: "word_family_member",
    RelationType.SYNONYM_OF.value: RelationType.SYNONYM_OF.value,
    RelationType.NEAR_SYNONYM_OF.value: RelationType.NEAR_SYNONYM_OF.value,
    RelationType.ANTONYM_OF.value: RelationType.ANTONYM_OF.value,
    RelationType.OPPOSITE_OF.value: RelationType.OPPOSITE_OF.value,
    RelationType.CONTRASTS_WITH.value: RelationType.CONTRASTS_WITH.value,
    RelationType.RELATED_TO.value: RelationType.RELATED_TO.value,
    RelationType.REALIZED_BY.value: "realizes",
    RelationType.MERGED_INTO.value: "merged_from",
    RelationType.SEMANTIC_BRIDGE.value: "bridged_by",
    RelationType.TRANSITION_TO.value: "transitioned_from",
}


# ---------------------------------------------------------------------------
# Closed value sets
#
# Derived from the enums so the two can never drift. Used to build CHECK
# constraints and shared with the API layer for validation.
# ---------------------------------------------------------------------------

WORLD_STATUS_VALUES = tuple(s.value for s in WorldStatus)
CLAIM_STATUS_VALUES = tuple(s.value for s in ClaimStatus)
SCOPE_VALUES = tuple(s.value for s in Scope)
CLAIM_TYPE_VALUES = tuple(s.value for s in ClaimType)
RELATION_TYPE_VALUES = tuple(s.value for s in RelationType)
CHALLENGE_STATUS_VALUES = tuple(s.value for s in ChallengeStatus)
CHALLENGE_RESOLUTION_VALUES = tuple(s.value for s in ChallengeResolution)

SUBJECT_KINDS = (
    "world",
    "lexical_form",
    "source",
    "witness",
    "segment",
    "unit",
    "relation",
    "path",
)

EMBEDDING_TYPES = (
    "world_full",
    "world_definition",
    "world_meaning",
    "world_literary",
    "world_philosophical",
    "world_modern",
    "world_questions",
    "claim_text",
    "claim_evidence",
    "source_segment",
    "source_translation",
)

EMBEDDING_ENTITY_TYPES = ("world", "claim", "source", "relation")

CHALLENGE_ENTITY_TYPES = ("world", "claim", "relation")


def _in_check(column: str, values: tuple[str, ...]) -> str:
    """Render a SQL ``IN`` predicate for a CHECK constraint."""

    rendered = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({rendered})"


def enum_column(*, index: bool = True, nullable: bool = False) -> Column:
    """Text column for a closed enumeration (Ontology v1.0 §2.1).

    SQLModel maps a ``StrEnum`` annotation to a SQLAlchemy ``Enum`` column,
    which persists the member *name* ("PROPOSED") rather than the *value*
    ("proposed"). That silently disagrees with the wire format and with the
    CHECK constraints. Declaring the column as ``Text`` stores the value,
    which is what the ontology specifies and what the API returns.
    """

    return Column(Text, nullable=nullable, index=index)


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

    __tablename__ = "worlds"
    __table_args__ = (
        CheckConstraint(_in_check("status", WORLD_STATUS_VALUES), name="worlds_status_chk"),
        CheckConstraint(_in_check("scope", SCOPE_VALUES), name="worlds_scope_chk"),
    )

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
    status: WorldStatus = SQLField(
        default=WorldStatus.PROPOSED, sa_column=enum_column()
    )
    scope: Scope = SQLField(default=Scope.GLOBAL, sa_column=enum_column())
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

class Relation(SQLModel, table=True):
    """A meaning-bearing connection between two Worlds. A governed knowledge assertion."""

    __tablename__ = "relations"
    __table_args__ = (
        CheckConstraint(
            _in_check("relation_type", RELATION_TYPE_VALUES), name="relations_type_chk"
        ),
        CheckConstraint(_in_check("status", WORLD_STATUS_VALUES), name="relations_status_chk"),
        CheckConstraint(_in_check("scope", SCOPE_VALUES), name="relations_scope_chk"),
        CheckConstraint(
            "source_world_id <> target_world_id", name="relations_no_self_chk"
        ),
    )

    relation_id: str = SQLField(primary_key=True, index=True)
    relation_type: str = SQLField(sa_column=enum_column())
    source_world_id: str = SQLField(foreign_key="worlds.world_id", index=True)
    target_world_id: str = SQLField(foreign_key="worlds.world_id", index=True)
    claim_id: str | None = None
    status: WorldStatus = SQLField(
        default=WorldStatus.PROPOSED, sa_column=enum_column()
    )
    scope: Scope = SQLField(default=Scope.GLOBAL, sa_column=enum_column())
    provenance: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# SemanticPath
# ---------------------------------------------------------------------------

class SemanticPath(SQLModel, table=True):
    """A first-class entity representing a meaningful journey through Worlds."""

    __tablename__ = "semantic_paths"
    __table_args__ = (
        CheckConstraint(_in_check("scope", SCOPE_VALUES), name="semantic_paths_scope_chk"),
    )

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

    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint(_in_check("claim_type", CLAIM_TYPE_VALUES), name="claims_type_chk"),
        CheckConstraint(_in_check("status", CLAIM_STATUS_VALUES), name="claims_status_chk"),
        CheckConstraint(_in_check("scope", SCOPE_VALUES), name="claims_scope_chk"),
        CheckConstraint(
            _in_check("subject_kind", SUBJECT_KINDS), name="claims_subject_kind_chk"
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0", name="claims_confidence_chk"
        ),
    )

    claim_id: str = SQLField(primary_key=True, index=True)
    claim_type: str = SQLField(sa_column=enum_column())
    subject_kind: str = SQLField(sa_column=enum_column())
    subject_reference_id: str = SQLField(index=True)
    subject_label: str | None = None
    predicate: str = SQLField(index=True)
    object: str | None = None
    text: str = SQLField(sa_column=Column(Text))
    status: str = SQLField(
        default=ClaimStatus.PROPOSED.value, sa_column=enum_column()
    )
    scope: str = SQLField(default=Scope.GLOBAL.value, sa_column=enum_column())
    confidence: float = SQLField(default=0.0)
    evidence: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    provenance: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    version_history: list[str] = SQLField(default=[], sa_column=Column(JSON))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# OntologyRegistry
# ---------------------------------------------------------------------------

class OntologyRegistryEntry(SQLModel, table=True):
    """Canonical World entry with aliases and translations."""

    __tablename__ = "ontology_registry"
    __table_args__ = (
        CheckConstraint(
            _in_check("status", WORLD_STATUS_VALUES), name="ontology_registry_status_chk"
        ),
    )

    world_id: str = SQLField(primary_key=True, index=True)
    canonical_term: str = SQLField(index=True)
    aliases: list[str] = SQLField(default=[], sa_column=Column(JSON))
    translations: dict[str, str] = SQLField(default={}, sa_column=Column(JSON))
    spellings: list[str] = SQLField(default=[], sa_column=Column(JSON))
    historical_forms: list[str] = SQLField(default=[], sa_column=Column(JSON))
    language_forms: dict[str, str] = SQLField(default={}, sa_column=Column(JSON))
    status: str = SQLField(
        default=WorldStatus.APPROVED.value, sa_column=enum_column()
    )
    extra_metadata: dict[str, Any] = SQLField(default={}, sa_column=Column(JSON))


# ---------------------------------------------------------------------------
# Embedding Provenance
# ---------------------------------------------------------------------------

class EmbeddingProvenance(SQLModel, table=True):
    """Provenance record for an embedding."""

    __tablename__ = "embedding_provenance"
    __table_args__ = (
        CheckConstraint(
            _in_check("entity_type", EMBEDDING_ENTITY_TYPES),
            name="embedding_provenance_entity_type_chk",
        ),
        CheckConstraint(
            _in_check("embedding_type", EMBEDDING_TYPES),
            name="embedding_provenance_type_chk",
        ),
    )

    embedding_id: str = SQLField(primary_key=True, index=True)
    entity_id: str = SQLField(index=True)
    entity_type: str = SQLField(sa_column=enum_column())
    embedding_type: str = SQLField(sa_column=enum_column())
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
    __table_args__ = (
        CheckConstraint(
            _in_check("entity_type", EMBEDDING_ENTITY_TYPES), name="embeddings_entity_type_chk"
        ),
        CheckConstraint(
            _in_check("embedding_type", EMBEDDING_TYPES), name="embeddings_type_chk"
        ),
    )

    embedding_id: str = SQLField(primary_key=True, index=True)
    entity_id: str = SQLField(index=True)
    entity_type: str = SQLField(sa_column=enum_column())
    embedding_type: str = SQLField(sa_column=enum_column())
    model: str
    model_version: str
    dimensions: int
    vector: list[float] = SQLField(sa_column=Column(EmbeddingVector(), nullable=False))
    source_version: str | None = None
    content_hash: str | None = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Challenge (Governance)
# ---------------------------------------------------------------------------

class Challenge(SQLModel, table=True):
    """A challenge to an approved entity (World, Claim, Relation)."""

    __tablename__ = "challenges"
    __table_args__ = (
        CheckConstraint(
            _in_check("entity_type", CHALLENGE_ENTITY_TYPES), name="challenges_entity_type_chk"
        ),
        CheckConstraint(
            _in_check("status", CHALLENGE_STATUS_VALUES), name="challenges_status_chk"
        ),
        CheckConstraint(
            "resolution IS NULL OR " + _in_check("resolution", CHALLENGE_RESOLUTION_VALUES),
            name="challenges_resolution_chk",
        ),
        CheckConstraint(
            "status <> 'resolved' OR (resolution IS NOT NULL "
            "AND resolver_id IS NOT NULL AND resolved_at IS NOT NULL)",
            name="challenges_resolved_complete_chk",
        ),
    )

    challenge_id: str = SQLField(primary_key=True, index=True)
    entity_type: str = SQLField(sa_column=enum_column())  # "world" | "claim" | "relation"
    entity_id: str = SQLField(index=True)
    challenger_id: str
    reason: str = SQLField(sa_column=Column(Text))
    new_evidence: list[dict[str, Any]] = SQLField(default=[], sa_column=Column(JSON))
    suggested_correction: dict[str, Any] | None = SQLField(default=None, sa_column=Column(JSON))
    status: str = SQLField(
        default=ChallengeStatus.OPEN.value, sa_column=enum_column()
    )
    resolution: str | None = SQLField(default=None, sa_column=enum_column(nullable=True))
    resolver_id: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


