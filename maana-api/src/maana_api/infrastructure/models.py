"""SQLModel database models for PostgreSQL."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Field, Relationship, SQLModel
import uuid


class WorldModel(SQLModel, table=True):
    __tablename__ = "worlds"

    world_id: str = Field(primary=True, index=True)
    canonical_term: str = Field(index=True)
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
    semantic_dimensions: dict[str, str] = Field(default={}, sa_column=Column(JSONB))
    status: str = Field(default="proposed", index=True)
    scope: str = Field(default="global", index=True)
    chapter_id: str | None = Field(default=None, index=True)
    cluster_id: str | None = Field(default=None, index=True)
    current_version_id: str | None = None
    version_history: list[str] = Field(default=[], sa_column=Column(JSONB))
    provenance: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ClaimModel(SQLModel, table=True):
    __tablename__ = "claims"

    claim_id: str = Field(primary=True, index=True)
    claim_type: str = Field(index=True)
    subject_kind: str
    subject_reference_id: str = Field(index=True)
    subject_label: str | None = None
    predicate: str = Field(index=True)
    object: str | None = None
    text: str = Field(sa_column=Column(Text))
    status: str = Field(default="proposed", index=True)
    scope: str = Field(default="global", index=True)
    confidence: float = Field(default=0.0)
    evidence: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    provenance: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RelationModel(SQLModel, table=True):
    __tablename__ = "relations"

    relation_id: str = Field(primary=True, index=True)
    relation_type: str = Field(index=True)
    source_world_id: str = Field(foreign_key="worlds.world_id", index=True)
    target_world_id: str = Field(foreign_key="worlds.world_id", index=True)
    claim_id: str | None = None
    status: str = Field(default="proposed", index=True)
    scope: str = Field(default="global", index=True)
    provenance: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChapterModel(SQLModel, table=True):
    __tablename__ = "chapters"

    chapter_id: str = Field(primary=True, index=True)
    title: str
    title_transliteration: str | None = None
    description: str | None = None
    central_question: str | None = None
    order: int = Field(index=True)
    metadata: dict[str, Any] = Field(default={}, sa_column=Column(JSONB))


class SemanticClusterModel(SQLModel, table=True):
    __tablename__ = "semantic_clusters"

    cluster_id: str = Field(primary=True, index=True)
    chapter_id: str = Field(foreign_key="chapters.chapter_id", index=True)
    part_id: str | None = None
    title: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default={}, sa_column=Column(JSONB))


class LexicalFormModel(SQLModel, table=True):
    __tablename__ = "lexical_forms"

    lexical_id: str = Field(primary=True, index=True)
    term: str = Field(index=True)
    language: str = Field(index=True)
    transliteration: str | None = None
    root: str | None = None
    metadata: dict[str, Any] = Field(default={}, sa_column=Column(JSONB))


class SemanticPathModel(SQLModel, table=True):
    __tablename__ = "semantic_paths"

    path_id: str = Field(primary=True, index=True)
    title: str
    description: str | None = None
    world_ids: list[str] = Field(default=[], sa_column=Column(JSONB))
    scope: str = Field(default="global", index=True)
    provenance: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OntologyRegistryEntryModel(SQLModel, table=True):
    __tablename__ = "ontology_registry"

    world_id: str = Field(primary=True, index=True)
    canonical_term: str = Field(index=True)
    aliases: list[str] = Field(default=[], sa_column=Column(JSONB))
    translations: dict[str, str] = Field(default={}, sa_column=Column(JSONB))
    spellings: list[str] = Field(default=[], sa_column=Column(JSONB))
    historical_forms: list[str] = Field(default=[], sa_column=Column(JSONB))
    language_forms: dict[str, str] = Field(default={}, sa_column=Column(JSONB))
    status: str = Field(default="approved", index=True)
    metadata: dict[str, Any] = Field(default={}, sa_column=Column(JSONB))


class EmbeddingProvenanceModel(SQLModel, table=True):
    __tablename__ = "embedding_provenance"

    embedding_id: str = Field(primary=True, index=True)
    entity_id: str = Field(index=True)
    entity_type: str = Field(index=True)
    embedding_type: str = Field(index=True)
    model: str
    model_version: str
    dimensions: int
    source_version: str | None = None
    content_hash: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
