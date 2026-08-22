"""Tests for services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import SQLModel, create_engine, Session

from maana_api.domain.models import Claim, ClaimStatus, ClaimType, Scope, World, WorldStatus
from maana_api.services.claim_service import ClaimService
from maana_api.services.world_service import WorldService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def _mock_graph():
    mock_graph = MagicMock()
    mock_graph.create_world_node = AsyncMock()
    with patch("maana_api.services.world_service.get_graph_projection", return_value=mock_graph):
        yield mock_graph


def test_create_world(session: Session):
    service = WorldService(session=session)
    world = World(
        world_id="W001",
        canonical_term="خیال",
        transliteration="Khayal",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    created = service.create_world(world)
    assert created.world_id == "W001"
    assert created.status == WorldStatus.PROPOSED


def test_get_world(session: Session):
    service = WorldService(session=session)
    world = World(
        world_id="W002",
        canonical_term="عشق",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    service.create_world(world)
    fetched = service.get_world("W002")
    assert fetched is not None
    assert fetched.canonical_term == "عشق"


def test_list_worlds(session: Session):
    service = WorldService(session=session)
    service.create_world(World(world_id="W003", canonical_term="A", status=WorldStatus.PROPOSED, scope=Scope.GLOBAL))
    service.create_world(World(world_id="W004", canonical_term="B", status=WorldStatus.APPROVED, scope=Scope.GLOBAL))
    worlds = service.list_worlds()
    assert len(worlds) == 2


def test_approve_world(session: Session):
    service = WorldService(session=session)
    world = World(
        world_id="W005",
        canonical_term="تصور",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    service.create_world(world)
    approved = service.approve_world("W005")
    assert approved.status == WorldStatus.APPROVED


def test_create_claim(session: Session):
    service = ClaimService(session=session)
    claim = Claim(
        claim_id="C001",
        claim_type=ClaimType.INTERPRETIVE,
        subject_kind="world",
        subject_reference_id="W001",
        predicate="DEEPENS_TOWARD",
        text="خیال deepens toward فنا.",
        status=ClaimStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    created = service.create_claim(claim)
    assert created.claim_id == "C001"


def test_get_claim(session: Session):
    service = ClaimService(session=session)
    claim = Claim(
        claim_id="C002",
        claim_type=ClaimType.INTERPRETIVE,
        subject_kind="world",
        subject_reference_id="W001",
        predicate="RELATED_TO",
        text="خیال is related to تصور.",
        status=ClaimStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    service.create_claim(claim)
    fetched = service.get_claim("C002")
    assert fetched is not None
    assert fetched.text == "خیال is related to تصور."


def test_approve_claim(session: Session):
    service = ClaimService(session=session)
    claim = Claim(
        claim_id="C003",
        claim_type=ClaimType.INTERPRETIVE,
        subject_kind="world",
        subject_reference_id="W001",
        predicate="RELATED_TO",
        text="خیال is related to تصور.",
        status=ClaimStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    service.create_claim(claim)
    approved = service.approve_claim("C003")
    assert approved.status == ClaimStatus.APPROVED
