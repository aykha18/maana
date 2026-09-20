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
    client.post(
        "/worlds/",
        json={
            "world_id": "W005",
            "canonical_term": "تصور",
            "status": "proposed",
            "scope": "global",
        },
    )
    response = client.post("/worlds/W005/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_create_claim(client: TestClient):
    response = client.post(
        "/claims/",
        json={
            "claim_id": "C001",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "subject_label": "خیال",
            "predicate": "DEEPENS_TOWARD",
            "object": "W002",
            "text": "خیال deepens toward فنا.",
            "status": "proposed",
            "scope": "global",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == "C001"
    assert data["claim_type"] == "interpretive"


def test_get_claim(client: TestClient):
    client.post(
        "/claims/",
        json={
            "claim_id": "C002",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "predicate": "RELATED_TO",
            "text": "خیال is related to تصور.",
            "status": "proposed",
            "scope": "global",
        },
    )
    response = client.get("/claims/C002")
    assert response.status_code == 200
    assert response.json()["text"] == "خیال is related to تصور."


def test_approve_claim(client: TestClient):
    client.post(
        "/claims/",
        json={
            "claim_id": "C003",
            "claim_type": "interpretive",
            "subject_kind": "world",
            "subject_reference_id": "W001",
            "predicate": "RELATED_TO",
            "text": "خیال is related to تصور.",
            "status": "proposed",
            "scope": "global",
        },
    )
    response = client.post("/claims/C003/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_create_relation(client: TestClient):
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
    client.post(
        "/relations/",
        json={
            "relation_id": "R005",
            "relation_type": "deepens",
            "source_world_id": "W001",
            "target_world_id": "W002",
            "status": "proposed",
            "scope": "global",
        },
    )
    response = client.post("/relations/R005/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
