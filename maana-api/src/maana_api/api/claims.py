"""Claim API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.domain.models import Challenge, ChallengeStatus, Claim, ClaimStatus, Scope
from maana_api.infrastructure.database import get_db_session
from maana_api.services.challenge_service import ChallengeService
from maana_api.services.claim_service import ClaimService

settings = get_settings()
router = APIRouter(prefix="/claims", tags=["claims"])


def get_claim_service(session: Session = Depends(get_db_session)) -> ClaimService:
    return ClaimService(session=session)


def get_challenge_service(session: Session = Depends(get_db_session)) -> ChallengeService:
    return ChallengeService(session=session)


@router.post("/", response_model=Claim, status_code=status.HTTP_201_CREATED)
def create_claim(claim: Claim, service: ClaimService = Depends(get_claim_service)) -> Claim:
    return service.create_claim(claim)


@router.get("/{claim_id}", response_model=Claim)
def get_claim(claim_id: str, service: ClaimService = Depends(get_claim_service)) -> Claim:
    claim = service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


@router.get("/", response_model=list[Claim])
def list_claims(
    status: ClaimStatus | None = None,
    scope: Scope | None = None,
    service: ClaimService = Depends(get_claim_service),
) -> list[Claim]:
    return service.list_claims(status=status, scope=scope)


@router.patch("/{claim_id}", response_model=Claim)
def update_claim(
    claim_id: str,
    updates: dict[str, Any],
    service: ClaimService = Depends(get_claim_service),
) -> Claim:
    claim = service.update_claim(claim_id, updates)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


@router.post("/{claim_id}/approve", response_model=Claim)
def approve_claim(claim_id: str, service: ClaimService = Depends(get_claim_service)) -> Claim:
    claim = service.approve_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


@router.post("/batch-approve", response_model=list[Claim])
def batch_approve_claims(
    claim_ids: list[str],
    service: ClaimService = Depends(get_claim_service),
) -> list[Claim]:
    results = []
    for claim_id in claim_ids:
        claim = service.approve_claim(claim_id)
        if claim is not None:
            results.append(claim)
    return results


@router.get("/{claim_id}/history", response_model=list[dict[str, Any]])
def get_claim_history(claim_id: str, service: ClaimService = Depends(get_claim_service)) -> list[dict[str, Any]]:
    claim = service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return [{"claim_id": claim_id, "note": "History endpoint - implement audit trail"}]


# Challenge endpoints
@router.post("/{claim_id}/challenge", response_model=Challenge, status_code=status.HTTP_201_CREATED)
def challenge_claim(
    claim_id: str,
    challenger_id: str,
    reason: str,
    new_evidence: list[dict[str, Any]] | None = None,
    suggested_correction: dict[str, Any] | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> Challenge:
    try:
        return service.create_challenge(
            entity_type="claim",
            entity_id=claim_id,
            challenger_id=challenger_id,
            reason=reason,
            new_evidence=new_evidence,
            suggested_correction=suggested_correction,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{claim_id}/challenges", response_model=list[Challenge])
def list_claim_challenges(
    claim_id: str,
    status: ChallengeStatus | None = None,
    service: ChallengeService = Depends(get_challenge_service),
) -> list[Challenge]:
    return service.list_challenges(entity_type="claim", entity_id=claim_id, status=status)
