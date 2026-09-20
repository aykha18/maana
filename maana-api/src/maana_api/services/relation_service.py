"""Relation service: lifecycle and graph projection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from maana_api.config import get_settings
from maana_api.domain.models import Relation, RelationType, WorldStatus, Scope
from maana_api.infrastructure.graph import get_graph_projection

settings = get_settings()


class RelationService:
    """Service for Relation lifecycle and graph projection."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._graph = get_graph_projection()

    def create_relation(self, relation: Relation) -> Relation:
        self._session.add(relation)
        self._session.commit()
        self._session.refresh(relation)
        return relation

    def get_relation(self, relation_id: str) -> Relation | None:
        statement = select(Relation).where(Relation.relation_id == relation_id)
        result = self._session.exec(statement).first()
        return result

    def list_relations(self, status: WorldStatus | None = None, scope: Scope | None = None) -> list[Relation]:
        statement = select(Relation)
        if status is not None:
            statement = statement.where(Relation.status == status)
        if scope is not None:
            statement = statement.where(Relation.scope == scope)
        return list(self._session.exec(statement).all())

    def update_relation(self, relation_id: str, updates: dict[str, Any]) -> Relation | None:
        relation = self.get_relation(relation_id)
        if relation is None:
            return None
        if relation.status not in (WorldStatus.DRAFT, WorldStatus.PROPOSED):
            raise ValueError(f"Cannot update Relation in status: {relation.status}")
        for key, value in updates.items():
            setattr(relation, key, value)
        self._session.add(relation)
        self._session.commit()
        self._session.refresh(relation)
        return relation

    def approve_relation(self, relation_id: str) -> Relation | None:
        relation = self.get_relation(relation_id)
        if relation is None:
            return None
        relation.status = WorldStatus.APPROVED
        self._session.add(relation)
        self._session.commit()
        self._session.refresh(relation)
        return relation