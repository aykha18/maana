"""Tests for the ontology invariants and the merge/split/versioning protocol.

Each test names the invariant from
``docs/04-ontology/Ontology_Knowledge_Model_v1.md`` that it exercises.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text as sql_text
from sqlmodel import Session, SQLModel, create_engine

from maana_api.domain.models import (
    Challenge,
    ChallengeResolution,
    Claim,
    ClaimStatus,
    ClaimType,
    Relation,
    RelationType,
    Scope,
    World,
    WorldStatus,
)
from maana_api.infrastructure.projection import pending_failures
from maana_api.services.challenge_service import ChallengeService
from maana_api.services.claim_service import ClaimService
from maana_api.services.relation_service import RelationService
from maana_api.services.validation import (
    InvariantViolation,
    resolve_scope_visibility,
)
from maana_api.services.world_service import WorldService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


PROVENANCE = [{"contributor_kind": "curator", "contributor_id": "t", "method": "test"}]
EVIDENCE = [
    {
        "evidence_id": "E1",
        "evidence_type": "text_span",
        "source_ref": "test://s/1",
        "text": "quoted",
    }
]


def world(world_id: str, term: str, status=WorldStatus.PROPOSED) -> World:
    return World(
        world_id=world_id,
        canonical_term=term,
        status=status,
        scope=Scope.GLOBAL,
        provenance=list(PROVENANCE),
    )


def claim(claim_id: str, subject_id: str, claim_type=ClaimType.INTERPRETIVE) -> Claim:
    return Claim(
        claim_id=claim_id,
        claim_type=claim_type.value,
        subject_kind="world",
        subject_reference_id=subject_id,
        predicate="deepens",
        text="assertion",
        status=ClaimStatus.PROPOSED.value,
        scope=Scope.GLOBAL.value,
        evidence=[dict(e) for e in EVIDENCE],
        provenance=list(PROVENANCE),
    )


def approved_pair(session: Session) -> tuple[WorldService, World, World]:
    service = WorldService(session=session)
    shouq = service.create_world(world("W_shouq", "شوق", WorldStatus.APPROVED))
    ishtiyaq = service.create_world(world("W_ishtiyaq", "اشتیاق", WorldStatus.APPROVED))
    return service, shouq, ishtiyaq


# ---------------------------------------------------------------- I-001, I-061


def test_merge_redirects_source_to_target_in_one_hop(session: Session):
    """I-061: a retired ID resolves to the surviving World in one hop."""

    service, shouq, ishtiyaq = approved_pair(session)
    service.merge_worlds("W_ishtiyaq", "W_shouq")

    source = service.get_world("W_ishtiyaq")
    assert source.status == WorldStatus.MERGED
    assert source.current_version_id == "W_shouq"

    resolved = service.resolve_world("W_ishtiyaq")
    assert resolved is not None and resolved.world_id == "W_shouq"


# ------------------------------------------------------------------- I-032


def test_merge_registers_alias_and_merged_into_relation(session: Session):
    """I-032: the retired ID becomes an alias and a MERGED_INTO Relation."""

    service, shouq, ishtiyaq = approved_pair(session)
    service.merge_worlds("W_ishtiyaq", "W_shouq")

    from maana_api.domain.models import OntologyRegistryEntry

    entry = session.get(OntologyRegistryEntry, "W_shouq")
    assert entry is not None
    assert "W_ishtiyaq" in entry.aliases

    relation = session.get(Relation, "R_W_ishtiyaq__merged_into__W_shouq")
    assert relation is not None
    assert relation.relation_type == RelationType.MERGED_INTO.value
    assert relation.source_world_id == "W_ishtiyaq"
    assert relation.target_world_id == "W_shouq"


# ------------------------------------------------------------------- I-059


def test_merge_repoints_claims_and_preserves_justification(session: Session):
    """I-059: nothing disappears; merge-justifying Claims are retained."""

    service, shouq, ishtiyaq = approved_pair(session)
    claims = ClaimService(session=session)
    claims.create_claim(claim("C_plain", "W_ishtiyaq"))
    claims.create_claim(
        claim("C_justification", "W_ishtiyaq", claim_type=ClaimType.COMPARATIVE)
    )

    service.merge_worlds("W_ishtiyaq", "W_shouq")

    assert claims.get_claim("C_plain").subject_reference_id == "W_shouq"
    # The claim that justifies the merge stays attached to the source.
    assert claims.get_claim("C_justification").subject_reference_id == "W_ishtiyaq"


def test_merge_repoints_relations_to_target(session: Session):
    """I-059: Relations survive the merge and follow the surviving World."""

    service, shouq, ishtiyaq = approved_pair(session)
    third = service.create_world(world("W_3", "سودا", WorldStatus.APPROVED))
    relations = RelationService(session=session)
    relations.create_relation(
        Relation(
            relation_id="R_a",
            relation_type=RelationType.DEEPENS.value,
            source_world_id="W_ishtiyaq",
            target_world_id="W_3",
            status=WorldStatus.PROPOSED,
        )
    )

    service.merge_worlds("W_ishtiyaq", "W_shouq")

    moved = session.get(Relation, "R_a")
    assert moved.source_world_id == "W_shouq"
    assert moved.target_world_id == "W_3"
    _ = third


# ------------------------------------------------------------------- I-060


def test_merge_rejects_already_merged_source(session: Session):
    """I-060: a merged World is never a merge source again."""

    service, shouq, ishtiyaq = approved_pair(session)
    other = service.create_world(world("W_other", "میل", WorldStatus.APPROVED))
    service.merge_worlds("W_ishtiyaq", "W_shouq")

    with pytest.raises(ValueError):
        service.merge_worlds("W_ishtiyaq", "W_other")


def test_merge_rejects_self_merge(session: Session):
    service, shouq, ishtiyaq = approved_pair(session)
    with pytest.raises(InvariantViolation) as excinfo:
        service.merge_worlds("W_shouq", "W_shouq")
    assert excinfo.value.invariant == "I-021"


# ------------------------------------------------------------------- I-021


def test_self_relation_is_rejected_by_check_constraint(session: Session):
    """I-021: source_world_id <> target_world_id is enforced by the database."""

    service, shouq, ishtiyaq = approved_pair(session)
    session.add(
        Relation(
            relation_id="R_self",
            relation_type=RelationType.DEEPENS.value,
            source_world_id="W_shouq",
            target_world_id="W_shouq",
            status=WorldStatus.PROPOSED,
        )
    )
    with pytest.raises(Exception):
        session.commit()


# ------------------------------------------------------------------- I-053


def test_supersede_creates_new_version_and_retires_original(session: Session):
    """I-053: versions are new IDs; the original row is retained."""

    service, shouq, ishtiyaq = approved_pair(session)
    successor = service.supersede_world(
        "W_shouq", "W_shouq_v2", {"short_definition": "corrected definition"}
    )

    assert successor.world_id == "W_shouq_v2"
    assert successor.short_definition == "corrected definition"
    assert successor.version_history == ["W_shouq"]

    original = service.get_world("W_shouq")
    assert original.status == WorldStatus.SUPERSEDED
    assert original.current_version_id == "W_shouq_v2"
    # The original identity is permanently the first version (I-053).
    assert service.get_world("W_shouq").canonical_term == "شوق"


def test_supersede_repoints_edges(session: Session):
    """I-057: edges follow the new version."""

    service, shouq, ishtiyaq = approved_pair(session)
    third = service.create_world(world("W_3", "سودا", WorldStatus.APPROVED))
    relations = RelationService(session=session)
    relations.create_relation(
        Relation(
            relation_id="R_in",
            relation_type=RelationType.DEEPENS.value,
            source_world_id="W_3",
            target_world_id="W_shouq",
            status=WorldStatus.PROPOSED,
        )
    )

    service.supersede_world("W_shouq", "W_shouq_v2")
    assert session.get(Relation, "R_in").target_world_id == "W_shouq_v2"
    _ = third


def test_supersede_rejects_existing_target(session: Session):
    service, shouq, ishtiyaq = approved_pair(session)
    with pytest.raises(ValueError):
        service.supersede_world("W_shouq", "W_ishtiyaq")


# ------------------------------------------------------------------- I-056


@pytest.fixture
def subject(session: Session) -> World:
    """A World for claim fixtures to assert about (Ontology I-039)."""

    return WorldService(session=session).create_world(world("W_a", "مقدمه"))


def test_approved_claim_content_is_frozen(session: Session, subject: World):
    """I-056: correcting an approved Claim requires a new version."""

    service = ClaimService(session=session)
    service.create_claim(claim("C1", "W_a"))
    service.approve_claim("C1")

    with pytest.raises(InvariantViolation) as excinfo:
        service.update_claim("C1", {"text": "rewritten after approval"})
    assert excinfo.value.invariant == "I-056"

    # A status-only transition is still permitted.
    updated = service.update_claim("C1", {"status": ClaimStatus.PUBLISHED.value})
    assert updated.status == ClaimStatus.PUBLISHED


# ------------------------------------------------------------------- I-014


def test_confidence_not_writable_before_review(session: Session, subject: World):
    """I-014: confidence is set by a curator during review, not at intake."""

    service = ClaimService(session=session)
    service.create_claim(claim("C1", "W_a"))
    with pytest.raises(InvariantViolation) as excinfo:
        service.update_claim("C1", {"confidence": 0.9})
    assert excinfo.value.invariant == "I-014"


# ------------------------------------------------------------------- I-047


def test_rejected_claim_is_retained(session: Session, subject: World):
    """I-047: rejected proposals stay in the audit trail."""

    service = ClaimService(session=session)
    service.create_claim(claim("C1", "W_a"))
    rejected = service.reject_claim("C1", resolver_id="curator-1")
    assert rejected.status == ClaimStatus.REJECTED
    assert service.get_claim("C1") is not None


# ------------------------------------------------------------------- I-056/I-064


def test_split_records_axis_and_creates_children(session: Session):
    """I-064: a split records its axis and the parent becomes a redirect."""

    service = WorldService(session=session)
    parent = service.create_world(world("W_parent", "عشق", WorldStatus.APPROVED))

    children = service.split_world(
        "W_parent",
        [
            {"world_id": "W_divine", "canonical_term": "عشق الهی"},
            {"world_id": "W_human", "canonical_term": "عشق انسانی"},
        ],
        axis="divine versus human",
    )

    assert [c.world_id for c in children] == ["W_divine", "W_human"]
    assert all(c.status == WorldStatus.APPROVED for c in children)
    assert service.get_world("W_parent").status == WorldStatus.MERGED
    assert service.get_world("W_parent").central_axis == "divine versus human"
    # The parent is retained, never deleted (I-062).
    assert parent is not None
    assert service.get_world("W_parent") is not None


def test_split_requires_axis(session: Session):
    """I-064: a split without a recorded axis is rejected."""

    service = WorldService(session=session)
    service.create_world(world("W_parent", "عشق", WorldStatus.APPROVED))
    with pytest.raises(InvariantViolation) as excinfo:
        service.split_world("W_parent", [{"world_id": "W_a", "canonical_term": "a"}])
    assert excinfo.value.invariant == "I-064"


def test_split_assigns_claims_to_exactly_one_child(session: Session):
    """I-063: every Claim is assigned to exactly one child."""

    service = WorldService(session=session)
    service.create_world(world("W_parent", "عشق", WorldStatus.APPROVED))
    claims = ClaimService(session=session)
    claims.create_claim(claim("C_a", "W_parent"))
    claims.create_claim(claim("C_b", "W_parent"))

    service.split_world(
        "W_parent",
        [
            {"world_id": "W_divine", "canonical_term": "عشق الهی", "claim_ids": ["C_a"]},
            {"world_id": "W_human", "canonical_term": "عشق انسانی", "claim_ids": ["C_b"]},
        ],
        axis="divine versus human",
    )

    assert claims.get_claim("C_a").subject_reference_id == "W_divine"
    assert claims.get_claim("C_b").subject_reference_id == "W_human"


def test_split_assigns_relations_to_exactly_one_child(session: Session):
    """I-063: relations are distributed, not inherited by the first child."""

    service = WorldService(session=session)
    service.create_world(world("W_parent", "عشق", WorldStatus.APPROVED))
    service.create_world(world("W_other", "فنا", WorldStatus.APPROVED))
    relations = RelationService(session=session)
    relations.create_relation(
        Relation(
            relation_id="R_a",
            relation_type=RelationType.DEEPENS.value,
            source_world_id="W_parent",
            target_world_id="W_other",
            status=WorldStatus.APPROVED,
            provenance=list(PROVENANCE),
        )
    )

    service.split_world(
        "W_parent",
        [
            {
                "world_id": "W_divine",
                "canonical_term": "عشق الهی",
                "relation_ids": ["R_a"],
            },
            {"world_id": "W_human", "canonical_term": "عشق انسانی"},
        ],
        axis="divine versus human",
    )

    moved = session.get(Relation, "R_a")
    assert moved.source_world_id == "W_divine"
    # The other endpoint is untouched, so the relation keeps its meaning.
    assert moved.target_world_id == "W_other"


def test_split_rejects_duplicate_claim_assignment(session: Session):
    """I-063: no Claim is duplicated across children."""

    service = WorldService(session=session)
    service.create_world(world("W_parent", "عشق", WorldStatus.APPROVED))
    claims = ClaimService(session=session)
    claims.create_claim(claim("C_a", "W_parent"))

    with pytest.raises(ValueError):
        service.split_world(
            "W_parent",
            [
                {"world_id": "W_x", "canonical_term": "x", "claim_ids": ["C_a"]},
                {"world_id": "W_y", "canonical_term": "y", "claim_ids": ["C_a"]},
            ],
            axis="an axis",
        )


# ------------------------------------------------------------------- I-052a


def test_world_status_has_no_challenged_value():
    """I-052a: a World is not less canonical because someone disputes it."""

    assert not hasattr(WorldStatus, "CHALLENGED")
    assert "challenged" not in {s.value for s in WorldStatus}
    assert "challenged" in {s.value for s in ClaimStatus}


def test_challenge_on_world_leaves_status_approved(session: Session):
    """I-052a: the open Challenge is the sole marker of contest for a World."""

    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق", WorldStatus.APPROVED))
    challenges = ChallengeService(session=session)
    challenge = challenges.create_challenge(
        entity_type="world",
        entity_id="W_a",
        challenger_id="reader-1",
        reason="this reading is contested",
    )
    assert challenge.status == "open"
    assert service.get_world("W_a").status == WorldStatus.APPROVED


# ------------------------------------------------------------------- I-027


def test_resolved_challenge_records_full_audit(session: Session):
    """I-027: resolution requires resolution, resolver, and timestamp."""

    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق", WorldStatus.APPROVED))
    challenges = ChallengeService(session=session)
    challenge = challenges.create_challenge(
        entity_type="world", entity_id="W_a", challenger_id="r", reason="contested"
    )
    resolved = challenges.resolve_challenge(
        challenge.challenge_id, ChallengeResolution.REAFFIRMED, resolver_id="curator-1"
    )
    assert resolved.status == "resolved"
    assert resolved.resolution == "reaffirmed"
    assert resolved.resolver_id == "curator-1"
    assert resolved.resolved_at is not None


# ------------------------------------------------------------------- §8.3


def test_challenge_supersede_creates_successor_at_proposed(session: Session):
    """Ontology §8.3: versioning is not approval; the successor is proposed."""

    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق", WorldStatus.APPROVED))
    challenges = ChallengeService(session=session)
    challenge = challenges.create_challenge(
        entity_type="world",
        entity_id="W_a",
        challenger_id="r",
        reason="definition is wrong",
        suggested_correction={"short_definition": "corrected"},
    )
    challenges.resolve_challenge(
        challenge.challenge_id,
        ChallengeResolution.SUPERSEDED,
        resolver_id="curator-1",
        new_entity_id="W_a_v2",
    )

    original = service.get_world("W_a")
    assert original.status == WorldStatus.SUPERSEDED
    assert "W_a_v2" in original.version_history

    successor = service.get_world("W_a_v2")
    assert successor is not None
    assert successor.status == WorldStatus.PROPOSED
    assert successor.short_definition == "corrected"
    assert successor.version_history == ["W_a"]


def test_challenge_supersede_rejects_reusing_an_existing_id(session: Session):
    """I-001: a version must have a new ID; an existing World cannot be reused."""

    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق", WorldStatus.APPROVED))
    service.create_world(world("W_b", "فنا", WorldStatus.APPROVED))
    challenges = ChallengeService(session=session)
    challenge = challenges.create_challenge(
        entity_type="world", entity_id="W_a", challenger_id="r", reason="wrong"
    )
    with pytest.raises(ValueError):
        challenges.resolve_challenge(
            challenge.challenge_id,
            ChallengeResolution.SUPERSEDED,
            resolver_id="curator-1",
            new_entity_id="W_b",
        )


# ------------------------------------------------------------------- §2.1


def test_enum_columns_store_values_not_names(session: Session):
    """Ontology §2.1: closed sets are stored as their lowercase values."""

    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق"))
    stored = session.exec(
        sql_text("SELECT status, scope FROM worlds WHERE world_id = 'W_a'")
    ).all()
    assert stored[0] == ("proposed", "global")


def test_check_constraint_rejects_unknown_status(session: Session):
    session.exec(sql_text("SELECT 1"))  # ensure connection
    with pytest.raises(Exception):
        session.add(
            World(
                world_id="W_bad",
                canonical_term="x",
                status=WorldStatus.PROPOSED,
                scope=Scope.GLOBAL,
                provenance=list(PROVENANCE),
            )
        )
        session.commit()
        session.exec(
            sql_text("UPDATE worlds SET status = 'not_a_status' WHERE world_id = 'W_bad'")
        )
        session.commit()


# ------------------------------------------------------------------- §9.2


def test_scope_visibility_orders_narrowest_first():
    """I-066: narrower scope shadows broader scope."""

    assert resolve_scope_visibility("global") == ["global"]
    assert resolve_scope_visibility("tradition") == ["tradition", "global"]
    assert resolve_scope_visibility("workspace") == ["workspace", "tradition", "global"]


def test_unknown_scope_is_rejected():
    with pytest.raises(InvariantViolation) as excinfo:
        resolve_scope_visibility("planetary")
    assert excinfo.value.invariant == "I-067"


# ------------------------------------------------------------------- I-018


def test_world_cannot_be_approved_without_provenance(session: Session):
    service = WorldService(session=session)
    service.create_world(World(world_id="W_a", canonical_term="عشق"))
    with pytest.raises(InvariantViolation) as excinfo:
        service.approve_world("W_a")
    assert excinfo.value.invariant == "I-018"


def test_relation_cannot_be_approved_without_provenance(session: Session):
    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق", WorldStatus.APPROVED))
    service.create_world(world("W_b", "فنا", WorldStatus.APPROVED))
    relations = RelationService(session=session)
    relations.create_relation(
        Relation(
            relation_id="R1",
            relation_type=RelationType.DEEPENS.value,
            source_world_id="W_a",
            target_world_id="W_b",
            status=WorldStatus.PROPOSED,
        )
    )
    with pytest.raises(InvariantViolation) as excinfo:
        relations.approve_relation("R1")
    assert excinfo.value.invariant == "I-018"


# ------------------------------------------------------------------- I-076


def test_approval_survives_projection_failure(session: Session, _mock_graph_projection):
    """I-076/I-077: PostgreSQL is authoritative; a graph failure is repairable."""

    _mock_graph_projection.create_world_node = AsyncMock(
        side_effect=RuntimeError("neo4j unreachable")
    )
    service = WorldService(session=session)
    service.create_world(world("W_a", "عشق"))
    approved = service.approve_world("W_a")

    # The governance decision stands.
    assert approved.status == WorldStatus.APPROVED
    assert service.get_world("W_a").status == WorldStatus.APPROVED

    # And the failure is recorded for repair rather than swallowed.
    failures = pending_failures()
    assert len(failures) == 1
    assert failures[0].entity_id == "W_a"
    assert "neo4j unreachable" in failures[0].error
