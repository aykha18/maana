"""Challenge API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.domain.models import Challenge, ChallengeResolution, ChallengeStatus
from maana_api.infrastructure.database import get_db_session
from maana_api.services.challenge_service import ChallengeService

settings = get_settings()
router = APIRouter(prefix="/challenges", tags=["challenges"])


def get_challenge_service(session: Session = Depends(get_db_session)) -> ChallengeService:
    return ChallengeService(session=session)


@router.post("/", response_model=Challenge, status_code=status.HTTP_201_CREATED)
def create_challenge(
    entity_type: str,
    entity_id: str,
    challenger_id: str,
    reason: str,
    new_evidence: list[dict[str, Any]] | None = None,
    suggested_correction: dict[str, Any] | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> Challenge:
    """Create a challenge against an approved entity."""
    try:
        return service.create_challenge(
            entity_type=entity_type,
            entity_id=entity_id,
            challenger_id=challenger_id,
            reason=reason,
            new_evidence=new_evidence,
            suggested_correction=suggested_correction,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{challenge_id}", response_model=Challenge)
def get_challenge(
    challenge_id: str,
    service: ChallengeService = Depends(get_challenge_service),
) -> Challenge:
    """Get a challenge by ID."""
    challenge = service.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    return challenge


@router.get("/", response_model=list[Challenge])
def list_challenges(
    entity_type: str | None = None,
    entity_id: str | None = None,
    status: ChallengeStatus | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> list[Challenge]:
    """List challenges with optional filters."""
    return service.list_challenges(entity_type=entity_type, entity_id=entity_id, status=status)


@router.post("/{challenge_id}/resolve", response_model=Challenge)
def resolve_challenge(
    challenge_id: str,
    resolution: ChallengeResolution,
    resolver_id: str,
    new_entity_id: str | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> Challenge:
    """Resolve a challenge."""
    try:
        return service.resolve_challenge(
            challenge_id=challenge_id,
            resolution=resolution,
            resolver_id=resolver_id,
            new_entity_id=new_entity_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Convenience endpoints for specific entity types
challenge_router = APIRouter()


def add_challenge_routes(router: APIRouter, entity_type: str, id_param: str):
    """Add challenge routes to an entity router."""

    @router.post(f"/{{{id_param}}}/challenge", response_model=Challenge, status_code=status.HTTP_201_CREATED)
    def challenge_entity(
        challenger_id: str,
        reason: str,
        new_evidence: list[dict[str, Any]] | None = None,
        suggested_correction: dict[str, Any] | None = None,
        service: ChallengeService = Depends(get_challenge_service),
        **kwargs,
    ) -> Challenge:
        entity_id = kwargs[id_param]
        try:
            return service.create_challenge(
                entity_type=entity_type,
                entity_id=entity_id,
                challenger_id=challenger_id,
                reason=reason,
                new_evidence=new_evidence,
                suggested_correction=suggested_correction,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.get(f"/{{{id_param}}}/challenges", response_model=list[Challenge])
    def list_entity_challenges(
        status: ChallengeStatus | None = None,
        service: ChallengeService = Depends(get_challenge_service),
        **kwargs,
    ) -> list[Challenge]:
        entity_id = kwargs[id_param]
        return service.list_challenges(entity_type=entity_type, entity_id=entity_id, status=status)


# Add to worlds, claims, relations routers
# Usage: add_challenge_routes(worlds_router, "world", "world_id")
#        add_challenge_routes(claims_router, "claim", "claim_id")
#        add_challenge_routes(relations_router, "relation", "relation_id")