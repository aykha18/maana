"""Tests for API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from maana_api.api.main import app
from maana_api.domain.models import Claim, ClaimType, Scope, World, WorldStatus
from maana_api.infrastructure.database import get_db_session
from maana_api.services.world_service import WorldService


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = get_session_override
    with patch("maana_api.services.world_service.get_graph_projection") as mock_graph:
        mock_graph.return_value = MagicMock()
        mock_graph.return_value.create_world_node = AsyncMock()
        yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True}


# A World cannot be canonized without provenance (Ontology I-018), and a Claim
# subject must resolve to a real World (I-039). These helpers build fixtures
# that satisfy both.
PROVENANCE = [{"contributor_kind": "editor", "contributor_id": "test", "method": "manual"}]
EVIDENCE = [
    {
        "evidence_id": "E001",
        "evidence_type": "text_span",
        "source_ref": "test://source/1",
        "text": "quoted",
    }
]


def ensure_world(client: TestClient, world_id: str, term: str) -> None:
    """Create a World if absent, with provenance so it can be approved."""
    existing = client.get(f"/worlds/{world_id}")
    if existing.status_code == 200:
        return
    response = client.post(
        "/worlds/",
        json={
            "world_id": world_id,
            "canonical_term": term,
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
        },
    )
    assert response.status_code == 201, response.text


def test_create_world(client: TestClient):
    response = client.post(
        "/worlds/",
        json={
            "world_id": "W001",
            "canonical_term": "خیال",
            "transliteration": "Khayal",
            "urdu_term": "خیال",
            "english_gloss": "Imagination",
            "status": "proposed",
            "scope": "global",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["canonical_term"] == "خیال"
    assert data["status"] == "proposed"


def test_get_world(client: TestClient):
    client.post(
        "/worlds/",
        json={
            "world_id": "W002",
            "canonical_term": "عشق",
            "status": "proposed",
            "scope": "global",
        },
    )
    response = client.get("/worlds/W002")
    assert response.status_code == 200
    assert response.json()["canonical_term"] == "عشق"


def test_list_worlds(client: TestClient):
    client.post(
        "/worlds/",
        json={
            "world_id": "W003",
            "canonical_term": "A",
            "status": "proposed",
            "scope": "global",
        },
    )
    client.post(
        "/worlds/",
        json={
            "world_id": "W004",
            "canonical_term": "B",
            "status": "approved",
            "scope": "global",
        },
    )
    response = client.get("/worlds/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_approve_world(client: TestClient):
    ensure_world(client, "W005", "تصور")
    response = client.post("/worlds/W005/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_approve_world_without_provenance_is_rejected(client: TestClient):
    """I-018 over the API: approval of an unprovenanced World must fail."""
    response = client.post(
        "/worlds/",
        json={
            "world_id": "W006",
            "canonical_term": "فنا",
            "status": "proposed",
            "scope": "global",
        },
    )
    assert response.status_code == 201
    approve = client.post("/worlds/W006/approve")
    assert approve.status_code >= 400


def test_create_claim(client: TestClient):
    ensure_world(client, "W001", "خیال")
    response = client.post(
        "/claims/",
        json={
            "claim_id": "C001",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "subject_label": "خیال",
            "predicate": "deepens",
            "object": "W002",
            "text": "خیال deepens toward فنا.",
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
            "evidence": EVIDENCE,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == "C001"
    assert data["claim_type"] == "interpretive"


def test_create_claim_with_unresolvable_subject_is_rejected(client: TestClient):
    """I-039 over the API: a dangling subject reference must not persist."""
    response = client.post(
        "/claims/",
        json={
            "claim_id": "C_dangling",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W_nonexistent",
            "predicate": "deepens",
            "text": "dangling",
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
        },
    )
    assert response.status_code >= 400


def test_get_claim(client: TestClient):
    ensure_world(client, "W001", "خیال")
    client.post(
        "/claims/",
        json={
            "claim_id": "C002",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "predicate": "related_to",
            "text": "خیال is related to تصور.",
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
        },
    )
    response = client.get("/claims/C002")
    assert response.status_code == 200
    assert response.json()["text"] == "خیال is related to تصور."


def test_approve_claim(client: TestClient):
    ensure_world(client, "W001", "خیال")
    client.post(
        "/claims/",
        json={
            "claim_id": "C003",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "predicate": "related_to",
            "text": "خیال is related to تصور.",
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
            "evidence": EVIDENCE,
        },
    )
    response = client.post("/claims/C003/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_approve_claim_without_evidence_is_rejected(client: TestClient):
    """I-049 over the API: assertion claims need evidence before approval."""
    ensure_world(client, "W001", "خیال")
    client.post(
        "/claims/",
        json={
            "claim_id": "C_no_evidence",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "predicate": "related_to",
            "text": "no evidence",
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
        },
    )
    response = client.post("/claims/C_no_evidence/approve")
    assert response.status_code >= 400


def test_create_relation(client: TestClient):
    ensure_world(client, "W001", "خیال")
    ensure_world(client, "W002", "تصور")
    response = client.post(
        "/relations/",
        json={
            "relation_id": "R001",
            "relation_type": "deepens",
            "source_world_id": "W001",
            "target_world_id": "W002",
            "status": "proposed",
            "scope": "global",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["relation_id"] == "R001"
    assert data["relation_type"] == "deepens"


def test_get_relation(client: TestClient):
    ensure_world(client, "W001", "خیال")
    ensure_world(client, "W003", "جمود")
    client.post(
        "/relations/",
        json={
            "relation_id": "R002",
            "relation_type": "related_to",
            "source_world_id": "W001",
            "target_world_id": "W003",
            "status": "proposed",
            "scope": "global",
        },
    )
    response = client.get("/relations/R002")
    assert response.status_code == 200
    assert response.json()["relation_type"] == "related_to"


def test_list_relations(client: TestClient):
    for wid, term in (("W001", "خیال"), ("W002", "تصور"), ("W004", "عشق"), ("W005", "فنا")):
        ensure_world(client, wid, term)
    client.post(
        "/relations/",
        json={
            "relation_id": "R003",
            "relation_type": "contrasts_with",
            "source_world_id": "W001",
            "target_world_id": "W004",
            "status": "proposed",
            "scope": "global",
        },
    )
    client.post(
        "/relations/",
        json={
            "relation_id": "R004",
            "relation_type": "part_of",
            "source_world_id": "W002",
            "target_world_id": "W005",
            "status": "approved",
            "scope": "global",
        },
    )
    response = client.get("/relations/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_approve_relation(client: TestClient):
    ensure_world(client, "W001", "خیال")
    ensure_world(client, "W002", "تصور")
    client.post(
        "/relations/",
        json={
            "relation_id": "R005",
            "relation_type": "deepens",
            "source_world_id": "W001",
            "target_world_id": "W002",
            "status": "proposed",
            "scope": "global",
            "provenance": PROVENANCE,
        },
    )
    response = client.post("/relations/R005/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_relation_with_dangling_endpoint_is_rejected(client: TestClient):
    """I-023 over the API: a Relation endpoint must resolve."""
    ensure_world(client, "W001", "خیال")
    response = client.post(
        "/relations/",
        json={
            "relation_id": "R_bad",
            "relation_type": "deepens",
            "source_world_id": "W001",
            "target_world_id": "W_nonexistent",
            "status": "proposed",
            "scope": "global",
        },
    )
    assert response.status_code >= 400
