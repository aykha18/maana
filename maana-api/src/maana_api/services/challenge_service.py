"""Challenge service: governance challenge lifecycle."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from maana_api.config import get_settings
from maana_api.domain.models import (
    Challenge,
    ChallengeResolution,
    ChallengeStatus,
    Claim,
    ClaimStatus,
    Relation,
    World,
    WorldStatus,
)

settings = get_settings()


class ChallengeService:
    """Service for challenge lifecycle and governance."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_challenge(
        self,
        entity_type: str,
        entity_id: str,
        challenger_id: str,
        reason: str,
        new_evidence: list[dict[str, Any]] | None = None,
        suggested_correction: dict[str, Any] | None = None,
    ) -> Challenge:
        """Create a challenge against an approved entity."""
        # Verify entity exists and is in challengeable state
        entity = self._get_entity(entity_type, entity_id)
        if entity is None:
            raise ValueError(f"Entity not found: {entity_type}:{entity_id}")

        # Check if entity is in a state that can be challenged
        if hasattr(entity, "status"):
            if entity_type == "world" and entity.status not in (WorldStatus.APPROVED, "challenged"):
                raise ValueError(f"World must be APPROVED to challenge, current: {entity.status}")
            if entity_type == "claim" and entity.status not in (ClaimStatus.APPROVED, ClaimStatus.CHALLENGED):
                raise ValueError(f"Claim must be APPROVED or CHALLENGED to challenge, current: {entity.status}")
            if entity_type == "relation" and entity.status not in (WorldStatus.APPROVED, "challenged"):
                raise ValueError(f"Relation must be APPROVED to challenge, current: {entity.status}")

        # Create challenge
        challenge = Challenge(
            challenge_id=f"ch_{entity_type}_{entity_id}_{challenger_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            challenger_id=challenger_id,
            reason=reason,
            new_evidence=new_evidence or [],
            suggested_correction=suggested_correction,
            status=ChallengeStatus.OPEN.value,
        )
        self._session.add(challenge)

        # Update entity status to CHALLENGED
        entity.status = self._get_challenged_status(entity_type)  # type: ignore
        entity.updated_at = datetime.utcnow()  # type: ignore
        self._session.add(entity)

        self._session.commit()
        self._session.refresh(challenge)
        return challenge

    def get_challenge(self, challenge_id: str) -> Challenge | None:
        """Get a challenge by ID."""
        statement = select(Challenge).where(Challenge.challenge_id == challenge_id)
        return self._session.exec(statement).first()

    def list_challenges(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        status: ChallengeStatus | None = None,
    ) -> list[Challenge]:
        """List challenges with optional filters."""
        statement = select(Challenge)
        if entity_type:
            statement = statement.where(Challenge.entity_type == entity_type)
        if entity_id:
            statement = statement.where(Challenge.entity_id == entity_id)
        if status:
            statement = statement.where(Challenge.status == status.value)
        return list(self._session.exec(statement).all())

    def resolve_challenge(
        self,
        challenge_id: str,
        resolution: ChallengeResolution,
        resolver_id: str,
        new_entity_id: str | None = None,
    ) -> Challenge:
        """Resolve a challenge."""
        challenge = self.get_challenge(challenge_id)
        if challenge is None:
            raise ValueError(f"Challenge not found: {challenge_id}")

        if challenge.status != ChallengeStatus.OPEN.value:
            raise ValueError(f"Challenge already resolved: {challenge.status}")

        entity = self._get_entity(challenge.entity_type, challenge.entity_id)
        if entity is None:
            raise ValueError(f"Entity no longer exists: {challenge.entity_type}:{challenge.entity_id}")

        # Apply resolution
        if resolution == ChallengeResolution.REAFFIRMED:
            # Original stands - revert to APPROVED
            entity.status = self._get_approved_status(challenge.entity_type)  # type: ignore
            entity.updated_at = datetime.utcnow()  # type: ignore
            self._session.add(entity)

        elif resolution == ChallengeResolution.SUPERSEDED:
            # New version should already be created by curator
            # Mark old as SUPERSEDED
            if not new_entity_id:
                raise ValueError("SUPERSEDED resolution requires new_entity_id")
            entity.status = self._get_superseded_status(challenge.entity_type)  # type: ignore
            entity.updated_at = datetime.utcnow()  # type: ignore
            # Link versions - create new list to ensure SQLModel tracks the change
            if hasattr(entity, "version_history"):
                entity.version_history = entity.version_history + [new_entity_id]  # type: ignore
            self._session.add(entity)

        elif resolution == ChallengeResolution.MERGED:
            if not new_entity_id:
                raise ValueError("MERGED resolution requires new_entity_id")
            entity.status = WorldStatus.MERGED  # type: ignore
            entity.updated_at = datetime.utcnow()  # type: ignore
            self._session.add(entity)

        elif resolution == ChallengeResolution.WITHDRAWN:
            # Challenger withdrew - revert to APPROVED
            entity.status = self._get_approved_status(challenge.entity_type)  # type: ignore
            entity.updated_at = datetime.utcnow()  # type: ignore
            self._session.add(entity)

        # Update challenge
        challenge.status = ChallengeStatus.RESOLVED.value
        challenge.resolution = resolution.value
        challenge.resolver_id = resolver_id
        challenge.resolved_at = datetime.utcnow()
        self._session.add(challenge)

        self._session.commit()
        self._session.refresh(challenge)
        return challenge

    def _get_entity(self, entity_type: str, entity_id: str):
        """Get entity by type and ID."""
        if entity_type == "world":
            statement = select(World).where(World.world_id == entity_id)
        elif entity_type == "claim":
            statement = select(Claim).where(Claim.claim_id == entity_id)
        elif entity_type == "relation":
            statement = select(Relation).where(Relation.relation_id == entity_id)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return self._session.exec(statement).first()

    def _get_challenged_status(self, entity_type: str) -> str:
        if entity_type == "world":
            return WorldStatus.APPROVED.value  # Worlds don't have CHALLENGED, use flag
        if entity_type == "claim":
            return ClaimStatus.CHALLENGED.value
        if entity_type == "relation":
            return WorldStatus.APPROVED.value  # Relations don't have CHALLENGED
        raise ValueError(f"Unknown entity type: {entity_type}")

    def _get_approved_status(self, entity_type: str) -> str:
        if entity_type == "world":
            return WorldStatus.APPROVED.value
        if entity_type == "claim":
            return ClaimStatus.APPROVED.value
        if entity_type == "relation":
            return WorldStatus.APPROVED.value
        raise ValueError(f"Unknown entity type: {entity_type}")

    def _get_superseded_status(self, entity_type: str) -> str:
        if entity_type == "world":
            return WorldStatus.SUPERSEDED.value
        if entity_type == "claim":
            return ClaimStatus.SUPERSEDED.value
        if entity_type == "relation":
            return WorldStatus.SUPERSEDED.value
        raise ValueError(f"Unknown entity type: {entity_type}")