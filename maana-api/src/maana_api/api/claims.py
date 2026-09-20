"""Claim API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.domain.models import Claim, ClaimStatus, Scope
from maana_api.infrastructure.database import get_db_session
from maana_api.services.claim_service import ClaimService

settings = get_settings()
router = APIRouter(prefix="/claims", tags=["claims"])


def get_claim_service(session: Session = Depends(get_db_session)) -> ClaimService:
    return ClaimService(session=session)


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
    # In a real implementation, this would query a history/audit table
    return [{"claim_id": claim_id, "note": "History endpoint - implement audit trail"}]
