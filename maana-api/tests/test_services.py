"""Tests for services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import SQLModel, create_engine, Session

from maana_api.domain.models import Claim, ClaimStatus, ClaimType, Scope, World, WorldStatus
from maana_api.services.claim_service import ClaimService
from maana_api.services.validation import InvariantViolation
from maana_api.services.world_service import WorldService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# A knowledge object with unknown origin cannot be canonized (Ontology I-018),
# so every World that reaches approval in these tests carries provenance.
PROVENANCE = [
    {
        "contributor_kind": "editor",
        "contributor_id": "test-editor",
        "method": "manual_entry",
    }
]

EVIDENCE = [
    {
        "evidence_id": "E001",
        "evidence_type": "text_span",
        "source_ref": "test://source/1",
        "text": "quoted passage",
    }
]


def make_world(world_id: str, term: str, status: WorldStatus = WorldStatus.PROPOSED) -> World:
    """A World that satisfies the pre-approval invariants."""
    return World(
        world_id=world_id,
        canonical_term=term,
        status=status,
        scope=Scope.GLOBAL,
        provenance=list(PROVENANCE),
    )


def make_claim(
    claim_id: str,
    subject_id: str = "W001",
    claim_type: ClaimType = ClaimType.INTERPRETIVE,
    status: str = ClaimStatus.PROPOSED.value,
    with_evidence: bool = True,
) -> Claim:
    """A Claim that satisfies the pre-approval invariants."""
    return Claim(
        claim_id=claim_id,
        claim_type=claim_type.value,
        subject_kind="world",
        subject_reference_id=subject_id,
        predicate="deepens",
        text="خیال deepens toward تصور.",
        status=status,
        scope=Scope.GLOBAL.value,
        evidence=[dict(e) for e in EVIDENCE] if with_evidence else [],
        provenance=list(PROVENANCE),
    )


@pytest.fixture
def subject_world(session: Session) -> World:
    """The World that claim fixtures assert about (Ontology I-039)."""
    return WorldService(session=session).create_world(make_world("W001", "خیال"))


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
    service.create_world(make_world("W005", "تصور"))
    approved = service.approve_world("W005")
    assert approved.status == WorldStatus.APPROVED


def test_approve_world_requires_provenance(session: Session):
    """I-018: a World with unknown origin cannot be canonized."""
    service = WorldService(session=session)
    service.create_world(
        World(world_id="W006", canonical_term="فنا", status=WorldStatus.PROPOSED)
    )
    with pytest.raises(InvariantViolation) as excinfo:
        service.approve_world("W006")
    assert excinfo.value.invariant == "I-018"


def test_create_claim(session: Session, subject_world: World):
    service = ClaimService(session=session)
    created = service.create_claim(make_claim("C001"))
    assert created.claim_id == "C001"


def test_create_claim_requires_resolvable_subject(session: Session):
    """I-039: a claim subject must resolve to a real entity."""
    service = ClaimService(session=session)
    with pytest.raises(InvariantViolation) as excinfo:
        service.create_claim(make_claim("C001", subject_id="W_does_not_exist"))
    assert excinfo.value.invariant == "I-039"


def test_get_claim(session: Session, subject_world: World):
    service = ClaimService(session=session)
    service.create_claim(make_claim("C002"))
    fetched = service.get_claim("C002")
    assert fetched is not None
    assert fetched.text == "خیال deepens toward تصور."


def test_approve_claim(session: Session, subject_world: World):
    service = ClaimService(session=session)
    service.create_claim(make_claim("C003"))
    approved = service.approve_claim("C003")
    assert approved.status == ClaimStatus.APPROVED


def test_approve_claim_requires_evidence(session: Session, subject_world: World):
    """I-049: assertion claims need evidence before approval."""
    service = ClaimService(session=session)
    service.create_claim(make_claim("C004", with_evidence=False))
    with pytest.raises(InvariantViolation) as excinfo:
        service.approve_claim("C004")
    assert excinfo.value.invariant == "I-049"


def test_approve_claim_without_evidence_allowed_for_editorial(
    session: Session, subject_world: World
):
    """I-049: editorial claims are authorized by the ontology itself."""
    service = ClaimService(session=session)
    service.create_claim(
        make_claim("C005", claim_type=ClaimType.EDITORIAL, with_evidence=False)
    )
    approved = service.approve_claim("C005")
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


def test_create_relation(session: Session, subject_world: World):
    from maana_api.services.relation_service import RelationService
    from maana_api.domain.models import Relation, RelationType

    service = RelationService(session=session)
    WorldService(session=session).create_world(make_world("W002", "تصور"))
    relation = Relation(
        relation_id="R001",
        relation_type=RelationType.DEEPENS.value,
        source_world_id="W001",
        target_world_id="W002",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
    )
    created = service.create_relation(relation)
    assert created.relation_id == "R001"


def test_create_relation_rejects_dangling_endpoint(session: Session, subject_world: World):
    """I-023: a Relation endpoint must resolve to a real World."""
    from maana_api.services.relation_service import RelationService
    from maana_api.domain.models import Relation, RelationType

    service = RelationService(session=session)
    with pytest.raises(InvariantViolation) as excinfo:
        service.create_relation(
            Relation(
                relation_id="R_bad",
                relation_type=RelationType.DEEPENS.value,
                source_world_id="W001",
                target_world_id="W_missing",
                status=WorldStatus.PROPOSED,
            )
        )
    assert excinfo.value.invariant == "I-023"


def test_approve_relation(session: Session, subject_world: World):
    from maana_api.services.relation_service import RelationService
    from maana_api.domain.models import Relation, RelationType

    service = RelationService(session=session)
    WorldService(session=session).create_world(make_world("W002", "تصور"))
    relation = Relation(
        relation_id="R002",
        relation_type=RelationType.RELATED_TO.value,
        source_world_id="W001",
        target_world_id="W002",
        status=WorldStatus.PROPOSED,
        scope=Scope.GLOBAL,
        provenance=list(PROVENANCE),
    )
    service.create_relation(relation)
    approved = service.approve_relation("R002")
    assert approved.status == WorldStatus.APPROVED


def test_create_challenge_on_claim(session: Session, subject_world: World):
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


def test_resolve_challenge_reaffirm(session: Session, subject_world: World):
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


def test_resolve_challenge_supersede(session: Session, subject_world: World):
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


def test_list_challenges(session: Session, subject_world: World):
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
