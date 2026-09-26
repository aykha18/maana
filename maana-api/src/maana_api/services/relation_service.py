"""Relation service: lifecycle and graph projection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from maana_api.config import get_settings
from maana_api.domain.models import Relation, RelationType, WorldStatus, Scope
from maana_api.domain.models import Claim, World
from maana_api.infrastructure.graph import get_graph_projection
from maana_api.infrastructure.projection import project
from maana_api.services.validation import (
    InvariantViolation,
    require_provenance,
    validate_scope_value,
)

settings = get_settings()


class RelationService:
    """Service for Relation lifecycle and graph projection."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._graph = get_graph_projection()

    def create_relation(self, relation: Relation) -> Relation:
        """Create a Relation, enforcing I-021 and I-023."""

        if relation.source_world_id == relation.target_world_id:
            raise InvariantViolation(
                "I-021", "a Relation may not connect a World to itself"
            )
        if relation.relation_type not in {r.value for r in RelationType}:
            raise InvariantViolation(
                "I-042", f"unknown relation_type {relation.relation_type!r}"
            )
        validate_scope_value(
            relation.scope.value if hasattr(relation.scope, "value") else relation.scope
        )
        self._require_world(relation.source_world_id)
        self._require_world(relation.target_world_id)
        if relation.claim_id is not None:
            if self._session.get(Claim, relation.claim_id) is None:
                raise InvariantViolation(
                    "I-023",
                    f"relation claims Claim {relation.claim_id!r}, which does not exist",
                )
        self._session.add(relation)
        self._session.commit()
        self._session.refresh(relation)
        return relation

    def _require_world(self, world_id: str) -> None:
        if self._session.get(World, world_id) is None:
            raise InvariantViolation(
                "I-023", f"World {world_id!r} does not exist"
            )

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
        """Approve a Relation, enforcing I-018, then project to the graph."""

        relation = self.get_relation(relation_id)
        if relation is None:
            return None
        require_provenance(relation)
        relation.status = WorldStatus.APPROVED
        self._session.add(relation)
        self._session.commit()
        self._session.refresh(relation)
        # A projection failure does not undo a governance decision: PostgreSQL
        # is authoritative and the edge is repairable (Ontology I-076, I-077).
        project(
            "create_relation",
            "relation",
            relation.relation_id,
            lambda: self._graph.create_relation(relation),
        )
        return relation