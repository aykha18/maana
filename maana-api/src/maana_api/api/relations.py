"""Relation API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.domain.models import Challenge, ChallengeStatus, Relation, RelationType, Scope, WorldStatus
from maana_api.infrastructure.database import get_db_session
from maana_api.services.challenge_service import ChallengeService
from maana_api.services.relation_service import RelationService

settings = get_settings()
router = APIRouter(prefix="/relations", tags=["relations"])


def get_relation_service(session: Session = Depends(get_db_session)) -> RelationService:
    return RelationService(session=session)


def get_challenge_service(session: Session = Depends(get_db_session)) -> ChallengeService:
    return ChallengeService(session=session)


@router.post("/", response_model=Relation, status_code=status.HTTP_201_CREATED)
def create_relation(relation: Relation, service: RelationService = Depends(get_relation_service)) -> Relation:
    return service.create_relation(relation)


@router.get("/{relation_id}", response_model=Relation)
def get_relation(relation_id: str, service: RelationService = Depends(get_relation_service)) -> Relation:
    relation = service.get_relation(relation_id)
    if relation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    return relation


@router.get("/", response_model=list[Relation])
def list_relations(
    status: WorldStatus | None = None,
    scope: Scope | None = None,
    service: RelationService = Depends(get_relation_service),
) -> list[Relation]:
    return service.list_relations(status=status, scope=scope)


@router.patch("/{relation_id}", response_model=Relation)
def update_relation(
    relation_id: str,
    updates: dict[str, Any],
    service: RelationService = Depends(get_relation_service),
) -> Relation:
    relation = service.update_relation(relation_id, updates)
    if relation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    return relation


@router.post("/{relation_id}/approve", response_model=Relation)
def approve_relation(relation_id: str, service: RelationService = Depends(get_relation_service)) -> Relation:
    relation = service.approve_relation(relation_id)
    if relation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    return relation


# Challenge endpoints
@router.post("/{relation_id}/challenge", response_model=Challenge, status_code=status.HTTP_201_CREATED)
def challenge_relation(
    relation_id: str,
    challenger_id: str,
    reason: str,
    new_evidence: list[dict[str, Any]] | None = None,
    suggested_correction: dict[str, Any] | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> Challenge:
    try:
        return service.create_challenge(
            entity_type="relation",
            entity_id=relation_id,
            challenger_id=challenger_id,
            reason=reason,
            new_evidence=new_evidence,
            suggested_correction=suggested_correction,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{relation_id}/challenges", response_model=list[Challenge])
def list_relation_challenges(
    relation_id: str,
    status: ChallengeStatus | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> list[Challenge]:
    return service.list_challenges(entity_type="relation", entity_id=relation_id, status=status)