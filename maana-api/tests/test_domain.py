"""Tests for domain models."""

from __future__ import annotations

import pytest
from maana_api.domain.models import (
    Claim,
    ClaimStatus,
    ClaimType,
    Evidence,
    EvidenceDimension,
    EvidenceType,
    ProvenanceRecord,
    Scope,
    World,
    WorldStatus,
)


def test_world_creation():
    world = World(
        world_id="W001",
        canonical_term="خیال",
        transliteration="Khayal",
        urdu_term="خیال",
        english_gloss="Imagination",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    assert world.status == WorldStatus.PROPOSED
    assert world.scope == Scope.GLOBAL
    assert world.canonical_term == "خیال"


def test_world_lifecycle():
    world = World(
        world_id="W002",
        canonical_term="عشق",
        status=WorldStatus.DRAFT,
    )
    assert world.status == WorldStatus.DRAFT


def test_claim_creation():
    claim = Claim(
        claim_id="C001",
        claim_type=ClaimType.INTERPRETIVE,
        subject={"kind": "world", "reference_id": "W001", "label": "خیال"},
        predicate="DEEPENS_TOWARD",
        object="W002",
        text="In Rumi's tradition, خیال deepens toward فنا.",
        status=ClaimStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    assert claim.status == ClaimStatus.PROPOSED
    assert claim.claim_type == ClaimType.INTERPRETIVE


def test_evidence_creation():
    evidence = Evidence(
        evidence_id="E001",
        evidence_type=EvidenceType.TEXT_SPAN,
        source_ref="minio://transcripts/lectures/abc/transcript.json",
        text="quoted passage here",
        start=120.5,
        end=125.3,
        dimensions={
            EvidenceDimension.SOURCE_AUTHORITY: 0.9,
            EvidenceDimension.DIRECTNESS: 0.8,
        },
    )
    assert evidence.evidence_type == EvidenceType.TEXT_SPAN
    assert evidence.dimensions[EvidenceDimension.SOURCE_AUTHORITY] == 0.9


def test_provenance_creation():
    provenance = ProvenanceRecord(
        contributor_kind="ai_system",
        contributor_id="extraction-pipeline-v2",
        method="llm_extraction",
        model="gpt-4o",
    )
    assert provenance.contributor_kind == "ai_system"


def test_scope():
    assert Scope.GLOBAL == "global"
    assert Scope.TRADITION == "tradition"
    assert Scope.WORKSPACE == "workspace"
