"""SemanticPath API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.domain.models import SemanticPath, Scope
from maana_api.infrastructure.database import get_db_session
from maana_api.services.path_service import SemanticPathService

settings = get_settings()
router = APIRouter(prefix="/paths", tags=["paths"])


def get_path_service(session: Session = Depends(get_db_session)) -> SemanticPathService:
    return SemanticPathService(session=session)


@router.post("/", response_model=SemanticPath, status_code=status.HTTP_201_CREATED)
def create_path(path: SemanticPath, service: SemanticPathService = Depends(get_path_service)) -> SemanticPath:
    return service.create_path(path)


@router.get("/{path_id}", response_model=SemanticPath)
def get_path(path_id: str, service: SemanticPathService = Depends(get_path_service)) -> SemanticPath:
    path = service.get_path(path_id)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SemanticPath not found")
    return path


@router.get("/", response_model=list[SemanticPath])
def list_paths(
    scope: Scope | None = None,
    service: SemanticPathService = Depends(get_path_service),
) -> list[SemanticPath]:
    return service.list_paths(scope=scope)


@router.patch("/{path_id}", response_model=SemanticPath)
def update_path(
    path_id: str,
    updates: dict[str, Any],
    service: SemanticPathService = Depends(get_path_service),
) -> SemanticPath:
    path = service.update_path(path_id, updates)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SemanticPath not found")
    return path