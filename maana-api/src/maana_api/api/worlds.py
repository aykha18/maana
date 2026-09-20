"""World API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.domain.models import Challenge, ChallengeStatus, Scope, World, WorldStatus
from maana_api.infrastructure.database import get_db_session
from maana_api.services.challenge_service import ChallengeService
from maana_api.services.world_service import WorldService

settings = get_settings()
router = APIRouter(prefix="/worlds", tags=["worlds"])


def get_world_service(session: Session = Depends(get_db_session)) -> WorldService:
    return WorldService(session=session)


def get_challenge_service(session: Session = Depends(get_db_session)) -> ChallengeService:
    return ChallengeService(session=session)


@router.post("/", response_model=World, status_code=status.HTTP_201_CREATED)
def create_world(world: World, service: WorldService = Depends(get_world_service)) -> World:
    return service.create_world(world)


@router.get("/{world_id}", response_model=World)
def get_world(world_id: str, service: WorldService = Depends(get_world_service)) -> World:
    world = service.get_world(world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return world


@router.get("/", response_model=list[World])
def list_worlds(
    status: WorldStatus | None = None,
    scope: Scope | None = None,
    service: WorldService = Depends(get_world_service),
) -> list[World]:
    return service.list_worlds(status=status, scope=scope)


@router.patch("/{world_id}", response_model=World)
def update_world(
    world_id: str,
    updates: dict[str, Any],
    service: WorldService = Depends(get_world_service),
) -> World:
    world = service.update_world(world_id, updates)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return world


@router.post("/{world_id}/approve", response_model=World)
def approve_world(world_id: str, service: WorldService = Depends(get_world_service)) -> World:
    world = service.approve_world(world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return world


@router.post("/{world_id}/deprecate", response_model=World)
def deprecate_world(world_id: str, service: WorldService = Depends(get_world_service)) -> World:
    world = service.deprecate_world(world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return world


@router.post("/merge", response_model=World)
def merge_worlds(
    source_id: str,
    target_id: str,
    service: WorldService = Depends(get_world_service),
) -> World:
    world = service.merge_worlds(source_id, target_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return world


@router.post("/batch-approve", response_model=list[World])
def batch_approve_worlds(
    world_ids: list[str],
    service: WorldService = Depends(get_world_service),
) -> list[World]:
    results = []
    for world_id in world_ids:
        world = service.approve_world(world_id)
        if world is not None:
            results.append(world)
    return results


@router.get("/{world_id}/history", response_model=list[dict[str, Any]])
def get_world_history(world_id: str, service: WorldService = Depends(get_world_service)) -> list[dict[str, Any]]:
    world = service.get_world(world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return [
        {"version_id": vid, "world_id": world_id}
        for vid in world.version_history
    ]


# Challenge endpoints
@router.post("/{world_id}/challenge", response_model=Challenge, status_code=status.HTTP_201_CREATED)
def challenge_world(
    world_id: str,
    challenger_id: str,
    reason: str,
    new_evidence: list[dict[str, Any]] | None = None,
    suggested_correction: dict[str, Any] | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> Challenge:
    try:
        return service.create_challenge(
            entity_type="world",
            entity_id=world_id,
            challenger_id=challenger_id,
            reason=reason,
            new_evidence=new_evidence,
            suggested_correction=suggested_correction,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{world_id}/challenges", response_model=list[Challenge])
def list_world_challenges(
    world_id: str,
    status: ChallengeStatus | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> list[Challenge]:
    return service.list_challenges(entity_type="world", entity_id=world_id, status=status)
