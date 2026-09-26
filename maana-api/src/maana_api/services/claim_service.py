"""Claim service: lifecycle and governance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from maana_api.domain.models import Claim, ClaimStatus
from maana_api.services.validation import (
    InvariantViolation,
    require_evidence_for_assertion,
    require_provenance,
    validate_scope_value,
    validate_subject_reference,
)

#: Statuses whose content is frozen. A published or approved Claim may only
#: change status; its assertion text is immutable (Ontology §7.2, I-056).
IMMUTABLE_CONTENT_STATUSES = frozenset(
    {
        ClaimStatus.APPROVED.value,
        ClaimStatus.PUBLISHED.value,
        ClaimStatus.SUPERSEDED.value,
    }
)

#: Statuses in which a curator may set confidence (I-014).
CONFIDENCE_WRITABLE_STATUSES = frozenset(
    {
        ClaimStatus.REVIEWED.value,
        ClaimStatus.APPROVED.value,
        ClaimStatus.PUBLISHED.value,
    }
)


class ClaimService:
    """Service for Claim lifecycle and governance."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_claim(self, claim_id: str) -> Claim | None:
        statement = select(Claim).where(Claim.claim_id == claim_id)
        return self._session.exec(statement).first()

    def list_claims(
        self, status: ClaimStatus | None = None, scope: str | None = None
    ) -> list[Claim]:
        statement = select(Claim)
        if status is not None:
            statement = statement.where(Claim.status == status.value)
        if scope is not None:
            statement = statement.where(Claim.scope == scope)
        return list(self._session.exec(statement).all())

    def list_claims_for_subject(
        self, subject_kind: str, subject_reference_id: str
    ) -> list[Claim]:
        """All claims asserting something about one entity (Ontology §3.11.2)."""

        statement = select(Claim).where(
            (Claim.subject_kind == subject_kind)
            & (Claim.subject_reference_id == subject_reference_id)
        )
        return list(self._session.exec(statement).all())

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create_claim(self, claim: Claim) -> Claim:
        """Create a Claim, validating its subject reference (I-039)."""
        validate_subject_reference(self._session, claim)
        if not 0.0 <= claim.confidence <= 1.0:
            raise InvariantViolation(
                "I-014", f"confidence {claim.confidence} outside [0.0, 1.0]"
            )
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def update_claim(self, claim_id: str, updates: dict[str, Any]) -> Claim | None:
        """Update a Claim.

        Content is editable only before approval. Once a Claim is approved or
        published, correcting it requires a new version through a challenge
        (Ontology §8.2), which preserves the audit trail instead of rewriting it.
        """

        claim = self.get_claim(claim_id)
        if claim is None:
            return None

        if claim.status in IMMUTABLE_CONTENT_STATUSES:
            content_fields = set(updates) - {"status"}
            if content_fields:
                raise InvariantViolation(
                    "I-056",
                    f"claim {claim_id} is {claim.status}; {sorted(content_fields)} "
                    "cannot be edited. Supersede it instead.",
                )

        if "confidence" in updates and claim.status not in CONFIDENCE_WRITABLE_STATUSES:
            raise InvariantViolation(
                "I-014",
                f"confidence may only be set while a claim is "
                f"{sorted(CONFIDENCE_WRITABLE_STATUSES)}; {claim_id} is {claim.status}",
            )

        if "subject_kind" in updates or "subject_reference_id" in updates:
            probe = Claim(
                claim_id=claim.claim_id,
                claim_type=claim.claim_type,
                subject_kind=updates.get("subject_kind", claim.subject_kind),
                subject_reference_id=updates.get(
                    "subject_reference_id", claim.subject_reference_id
                ),
                predicate=claim.predicate,
                text=claim.text,
            )
            validate_subject_reference(self._session, probe)

        for key, value in updates.items():
            setattr(claim, key, value)
        claim.updated_at = datetime.utcnow()
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def approve_claim(self, claim_id: str) -> Claim | None:
        """Approve a Claim, enforcing provenance and evidence requirements."""
        claim = self.get_claim(claim_id)
        if claim is None:
            return None
        require_provenance(claim)
        require_evidence_for_assertion(claim)
        claim.status = ClaimStatus.APPROVED
        claim.updated_at = datetime.utcnow()
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def reject_claim(self, claim_id: str, resolver_id: str) -> Claim | None:
        """Reject a Claim. The record is retained as audit history (I-047)."""

        claim = self.get_claim(claim_id)
        if claim is None:
            return None
        claim.status = ClaimStatus.REJECTED
        claim.updated_at = datetime.utcnow()
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def supersede_claim(
        self, claim_id: str, new_claim_id: str, corrections: dict[str, Any] | None = None
    ) -> Claim | None:
        """Create a new version of a Claim and retire the original (I-053)."""

        original = self.get_claim(claim_id)
        if original is None:
            return None
        if new_claim_id == claim_id:
            raise InvariantViolation("I-001", "a version must have a new ID")
        if original.status == ClaimStatus.SUPERSEDED:
            raise ValueError(f"Claim already superseded: {claim_id}")
        if self.get_claim(new_claim_id) is not None:
            raise ValueError(f"Target version already exists: {new_claim_id}")

        successor = Claim(
            claim_id=new_claim_id,
            claim_type=original.claim_type,
            subject_kind=original.subject_kind,
            subject_reference_id=original.subject_reference_id,
            subject_label=original.subject_label,
            predicate=original.predicate,
            object=original.object,
            text=original.text,
            status=original.status,
            scope=original.scope,
            confidence=original.confidence,
            evidence=[dict(e) for e in (original.evidence or [])],
            provenance=[dict(p) for p in (original.provenance or [])],
            version_history=list(original.version_history or []) + [claim_id],
        )
        if corrections:
            for key, value in corrections.items():
                setattr(successor, key, value)

        require_provenance(successor)
        require_evidence_for_assertion(successor)

        original.status = ClaimStatus.SUPERSEDED
        original.updated_at = datetime.utcnow()
        successor.updated_at = datetime.utcnow()

        self._session.add(successor)
        self._session.add(original)
        self._session.commit()
        self._session.refresh(successor)
        self._session.refresh(original)
        return successor
