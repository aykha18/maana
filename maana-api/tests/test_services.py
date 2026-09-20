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


def test_merge_worlds(session: Session):
    service = WorldService(session=session)
    # Create two approved worlds
    world1 = World(world_id="W100", canonical_term="شوق", status=WorldStatus.APPROVED, scope=Scope.GLOBAL)
    world2 = World(world_id="W101", canonical_term="اشتیاق", status=WorldStatus.APPROVED, scope=Scope.GLOBAL)
    service.create_world(world1)
    service.create_world(world2)
    
    # Merge W101 into W100
    result = service.merge_worlds("W101", "W100")
    assert result is not None
    assert result.world_id == "W100"
    
    # Source should be marked as MERGED
    merged = service.get_world("W101")
    assert merged is not None
    assert merged.status == WorldStatus.MERGED


def test_create_relation(session: Session):
    from maana_api.services.relation_service import RelationService
    from maana_api.domain.models import Relation, RelationType
    
    service = RelationService(session=session)
    relation = Relation(
        relation_id="R001",
        relation_type=RelationType.DEEPENS,
        source_world_id="W001",
        target_world_id="W002",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    created = service.create_relation(relation)
    assert created.relation_id == "R001"


def test_approve_relation(session: Session):
    from maana_api.services.relation_service import RelationService
    from maana_api.domain.models import Relation, RelationType
    
    service = RelationService(session=session)
    relation = Relation(
        relation_id="R002",
        relation_type=RelationType.RELATED_TO,
        source_world_id="W001",
        target_world_id="W002",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    service.create_relation(relation)
    approved = service.approve_relation("R002")
    assert approved.status == WorldStatus.APPROVED


def test_create_challenge_on_claim(session: Session):
    from maana_api.services.challenge_service import ChallengeService
    from maana_api.domain.models import Challenge, ChallengeStatus, Claim, ClaimStatus
    
    # Create and approve a claim first
    claim_service = ClaimService(session=session)
    claim = Claim(
        claim_id="C100",
        claim_type="interpretive",
        subject_kind="world",
        subject_reference_id="W001",
        predicate="RELATED_TO",
        text="Test claim",
        status=ClaimStatus.APPROVED,
        scope=Scope.GLOBAL,
    )
    claim_service.create_claim(claim)
    
    # Create challenge
    challenge_service = ChallengeService(session=session)
    challenge = challenge_service.create_challenge(
        entity_type="claim",
        entity_id="C100",
        challenger_id="reader_001",
        reason="Evidence contradicts this claim",
        new_evidence=[{"source": "manuscript_X", "text": "contradictory text"}],
    )
    
    assert challenge.challenge_id == "ch_claim_C100_reader_001"
    assert challenge.status == ChallengeStatus.OPEN.value
    assert challenge.entity_type == "claim"
    assert challenge.entity_id == "C100"
    
    # Claim status should be CHALLENGED
    challenged_claim = claim_service.get_claim("C100")
    assert challenged_claim is not None
    assert challenged_claim.status == ClaimStatus.CHALLENGED.value


def test_resolve_challenge_reaffirm(session: Session):
    from maana_api.services.challenge_service import ChallengeService
    from maana_api.domain.models import Challenge, ChallengeResolution, ChallengeStatus, Claim, ClaimStatus
    
    # Setup: claim + challenge
    claim_service = ClaimService(session=session)
    claim = Claim(
        claim_id="C101",
        claim_type="interpretive",
        subject_kind="world",
        subject_reference_id="W001",
        predicate="RELATED_TO",
        text="Test claim for reaffirm",
        status=ClaimStatus.APPROVED,
        scope=Scope.GLOBAL,
    )
    claim_service.create_claim(claim)
    
    challenge_service = ChallengeService(session=session)
    challenge = challenge_service.create_challenge(
        entity_type="claim",
        entity_id="C101",
        challenger_id="reader_002",
        reason="Disagree",
    )
    
    # Resolve with REAFFIRMED
    resolved = challenge_service.resolve_challenge(
        challenge_id=challenge.challenge_id,
        resolution=ChallengeResolution.REAFFIRMED,
        resolver_id="curator_001",
    )
    
    assert resolved.status == ChallengeStatus.RESOLVED.value
    assert resolved.resolution == ChallengeResolution.REAFFIRMED.value
    assert resolved.resolver_id == "curator_001"
    
    # Claim should be back to APPROVED
    claim = claim_service.get_claim("C101")
    assert claim.status == ClaimStatus.APPROVED.value


def test_resolve_challenge_supersede(session: Session):
    from maana_api.services.challenge_service import ChallengeService
    from maana_api.domain.models import Challenge, ChallengeResolution, ChallengeStatus, Claim, ClaimStatus
    
    # Setup: claim + challenge
    claim_service = ClaimService(session=session)
    claim = Claim(
        claim_id="C102",
        claim_type="interpretive",
        subject_kind="world",
        subject_reference_id="W001",
        predicate="RELATED_TO",
        text="Test claim for supersede",
        status=ClaimStatus.APPROVED,
        scope=Scope.GLOBAL,
    )
    claim_service.create_claim(claim)
    
    challenge_service = ChallengeService(session=session)
    challenge = challenge_service.create_challenge(
        entity_type="claim",
        entity_id="C102",
        challenger_id="reader_003",
        reason="Wrong interpretation",
    )
    
    # Resolve with SUPERSEDED (new claim C103 created by curator)
    resolved = challenge_service.resolve_challenge(
        challenge_id=challenge.challenge_id,
        resolution=ChallengeResolution.SUPERSEDED,
        resolver_id="curator_002",
        new_entity_id="C103",
    )
    
    assert resolved.resolution == ChallengeResolution.SUPERSEDED.value
    
    # Original claim should be SUPERSEDED
    claim = claim_service.get_claim("C102")
    assert claim.status == ClaimStatus.SUPERSEDED.value
    assert "C103" in claim.version_history


def test_list_challenges(session: Session):
    from maana_api.services.challenge_service import ChallengeService
    from maana_api.domain.models import Challenge, ChallengeStatus, Claim, ClaimStatus
    
    claim_service = ClaimService(session=session)
    claim = Claim(
        claim_id="C104",
        claim_type="interpretive",
        subject_kind="world",
        subject_reference_id="W001",
        predicate="RELATED_TO",
        text="Test claim for listing",
        status=ClaimStatus.APPROVED,
        scope=Scope.GLOBAL,
    )
    claim_service.create_claim(claim)
    
    challenge_service = ChallengeService(session=session)
    challenge_service.create_challenge("claim", "C104", "reader_1", "Reason 1")
    challenge_service.create_challenge("claim", "C104", "reader_2", "Reason 2")
    
    challenges = challenge_service.list_challenges(entity_type="claim", entity_id="C104")
    assert len(challenges) == 2
    
    open_challenges = challenge_service.list_challenges(entity_type="claim", entity_id="C104", status=ChallengeStatus.OPEN)
    assert len(open_challenges) == 2
