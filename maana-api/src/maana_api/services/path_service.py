"""SemanticPath service: lifecycle."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from maana_api.config import get_settings
from maana_api.domain.models import SemanticPath, Scope

settings = get_settings()


class SemanticPathService:
    """Service for SemanticPath lifecycle."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_path(self, path: SemanticPath) -> SemanticPath:
        self._session.add(path)
        self._session.commit()
        self._session.refresh(path)
        return path

    def get_path(self, path_id: str) -> SemanticPath | None:
        statement = select(SemanticPath).where(SemanticPath.path_id == path_id)
        result = self._session.exec(statement).first()
        return result

    def list_paths(self, scope: Scope | None = None) -> list[SemanticPath]:
        statement = select(SemanticPath)
        if scope is not None:
            statement = statement.where(SemanticPath.scope == scope)
        return list(self._session.exec(statement).all())

    def update_path(self, path_id: str, updates: dict[str, Any]) -> SemanticPath | None:
        path = self.get_path(path_id)
        if path is None:
            return None
        for key, value in updates.items():
            setattr(path, key, value)
        self._session.add(path)
        self._session.commit()
        self._session.refresh(path)
        return path