"""Claim service: lifecycle and governance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from maana_api.domain.models import Claim, ClaimStatus
from maana_api.infrastructure.database import get_sync_engine


class ClaimService:
    """Service for Claim lifecycle and governance."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_claim(self, claim: Claim) -> Claim:
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def get_claim(self, claim_id: str) -> Claim | None:
        statement = select(Claim).where(Claim.claim_id == claim_id)
        result = self._session.exec(statement).first()
        return result

    def list_claims(self, status: ClaimStatus | None = None, scope: str | None = None) -> list[Claim]:
        statement = select(Claim)
        if status is not None:
            statement = statement.where(Claim.status == status.value)
        if scope is not None:
            statement = statement.where(Claim.scope == scope)
        return list(self._session.exec(statement).all())

    def update_claim(self, claim_id: str, updates: dict[str, Any]) -> Claim | None:
        claim = self.get_claim(claim_id)
        if claim is None:
            return None
        for key, value in updates.items():
            setattr(claim, key, value)
        claim.updated_at = datetime.utcnow()
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim

    def approve_claim(self, claim_id: str) -> Claim | None:
        claim = self.get_claim(claim_id)
        if claim is None:
            return None
        claim.status = ClaimStatus.APPROVED
        claim.updated_at = datetime.utcnow()
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim
