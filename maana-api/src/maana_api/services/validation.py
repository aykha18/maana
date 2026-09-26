"""Invariant enforcement shared by the service layer.

Every function here exists to make a rule from
``docs/04-ontology/Ontology_Knowledge_Model_v1.md`` enforceable at the write
path. The rules are cited by invariant number so that a failure names the
specification it violates.
"""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from maana_api.domain.models import (
    Claim,
    ClaimType,
    Relation,
    Scope,
    SemanticPath,
    SUBJECT_KINDS,
    World,
)


class InvariantViolation(ValueError):
    """Raised when a write would violate a frozen ontology invariant."""

    def __init__(self, invariant: str, message: str) -> None:
        self.invariant = invariant
        super().__init__(f"[{invariant}] {message}")


#: Maps a Claim subject kind to the model it must resolve to (Ontology §4.5).
SUBJECT_MODEL_BY_KIND: dict[str, type] = {
    "world": World,
    "relation": Relation,
    "path": SemanticPath,
}

#: Subject kinds whose tables do not exist yet. A reference to one of these is
#: not validated rather than being rejected, so that the lecture pipeline can
#: stage claims about sources and texts before those tables are built.
DEFERRED_SUBJECT_KINDS = frozenset(
    {"source", "witness", "segment", "unit", "lexical_form"}
)


def validate_subject_reference(session: Session, claim: Claim) -> None:
    """Enforce I-039 / I-070: a subject must resolve to its declared kind.

    Polymorphic references cannot be expressed as a database foreign key, so
    every write path must check them. An unresolvable subject rejects the write
    rather than persisting a dangling pointer.
    """

    if claim.subject_kind not in SUBJECT_KINDS:
        raise InvariantViolation(
            "I-039",
            f"unknown subject_kind {claim.subject_kind!r}; "
            f"expected one of {', '.join(SUBJECT_KINDS)}",
        )

    if claim.subject_kind in DEFERRED_SUBJECT_KINDS:
        return

    model = SUBJECT_MODEL_BY_KIND[claim.subject_kind]
    key = _primary_key_of(model)
    resolved = session.get(model, claim.subject_reference_id)
    if resolved is None:
        raise InvariantViolation(
            "I-039",
            f"{claim.subject_kind} {claim.subject_reference_id!r} does not exist; "
            "a claim subject must resolve to a real entity",
        )
    _ = key


def _primary_key_of(model: type) -> str:
    return next(iter(model.__table__.primary_key.columns)).name


def require_provenance(record: Any, *, invariant: str = "I-018") -> None:
    """Enforce I-018: a record cannot be canonized without provenance.

    Applies to World, Claim, Relation, and SemanticPath. Governance decisions
    about structure (``editorial``, ``ontological`` claims) are exempt from the
    evidence requirement but never from the provenance requirement.
    """

    provenance = getattr(record, "provenance", None)
    if not provenance:
        raise InvariantViolation(
            invariant,
            f"{type(record).__name__} {getattr(record, 'world_id', None) or getattr(record, 'claim_id', None) or getattr(record, 'relation_id', None) or getattr(record, 'path_id', None)}"
            f" has no provenance; a knowledge object with unknown origin "
            "cannot be canonized",
        )


def require_evidence_for_assertion(claim: Claim) -> None:
    """Enforce I-049: assertion claims need evidence before approval.

    ``editorial`` and ``ontological`` claims are governance decisions about
    structure rather than assertions about content, so the ontology itself
    authorizes them.
    """

    if claim.claim_type in (
        ClaimType.EDITORIAL.value,
        ClaimType.ONTOLOGICAL.value,
    ):
        return
    if not claim.evidence:
        raise InvariantViolation(
            "I-049",
            f"claim {claim.claim_id} is type {claim.claim_type!r} and carries no "
            "evidence; assertion claims require evidence before approval",
        )


def validate_scope_value(scope: str) -> str:
    """Return ``scope`` if it is a known Scope value, else raise."""

    if scope not in {s.value for s in Scope}:
        raise InvariantViolation(
            "I-067", f"unknown scope {scope!r}"
        )
    return scope


def resolve_scope_visibility(requested: str) -> list[str]:
    """Scopes visible to a reader at ``requested``, narrowest first (§9.2).

    A read at ``workspace`` sees workspace, then tradition, then global. A read
    at ``global`` sees only global: inheritance flows inward-to-outward, so a
    global reader is not automatically a reader of narrower scopes. Narrow
    scope shadows broad scope for the same entity, so callers should evaluate
    results in the order returned here (I-066).
    """

    narrow_to_broad = [Scope.WORKSPACE.value, Scope.TRADITION.value, Scope.GLOBAL.value]
    if requested not in narrow_to_broad:
        raise InvariantViolation("I-067", f"unknown scope {requested!r}")
    return narrow_to_broad[narrow_to_broad.index(requested) :]
