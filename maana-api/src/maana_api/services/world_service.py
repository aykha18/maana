"""World service: lifecycle, governance, and projection."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from maana_api.config import get_settings
from maana_api.domain.models import (
    Chapter,
    World,
    WorldStatus,
    Scope,
    Relation,
    RelationType,
    SemanticCluster,
)
from maana_api.infrastructure.database import get_sync_engine
from maana_api.infrastructure.graph import get_graph_projection
from maana_api.infrastructure.vector_store import get_vector_store

settings = get_settings()


class WorldService:
    """Service for World lifecycle, governance, and projection."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._graph = get_graph_projection()
        self._vector = get_vector_store(session)

    def create_world(self, world: World) -> World:
        """Create a new World in PROPOSED state."""
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    def get_world(self, world_id: str) -> World | None:
        """Get a World by ID."""
        statement = select(World).where(World.world_id == world_id)
        result = self._session.exec(statement).first()
        return result

    def list_worlds(self, status: WorldStatus | None = None, scope: Scope | None = None) -> list[World]:
        """List Worlds with optional filters."""
        statement = select(World)
        if status is not None:
            statement = statement.where(World.status == status)
        if scope is not None:
            statement = statement.where(World.scope == scope)
        return list(self._session.exec(statement).all())

    def update_world(self, world_id: str, updates: dict[str, Any]) -> World | None:
        """Update a World. Only PROPOSED or DRAFT Worlds are mutable."""
        world = self.get_world(world_id)
        if world is None:
            return None
        if world.status not in (WorldStatus.DRAFT, WorldStatus.PROPOSED):
            raise ValueError(f"Cannot update World in status: {world.status}")
        for key, value in updates.items():
            setattr(world, key, value)
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    def approve_world(self, world_id: str) -> World | None:
        """Approve a World, project to graph, and generate embeddings."""
        world = self.get_world(world_id)
        if world is None:
            return None
        world.status = WorldStatus.APPROVED
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        # Project to graph
        asyncio_run(self._graph.create_world_node(world))
        # Generate and store embeddings (placeholder)
        # self._vector.upsert([...])
        return world

    def deprecate_world(self, world_id: str) -> World | None:
        """Deprecate a World."""
        world = self.get_world(world_id)
        if world is None:
            return None
        world.status = WorldStatus.DEPRECATED
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    def merge_worlds(self, source_id: str, target_id: str) -> World | None:
        """Merge source World into target World. Nothing disappears."""
        source = self.get_world(source_id)
        target = self.get_world(target_id)
        if source is None or target is None:
            return None
        if source.status != WorldStatus.APPROVED or target.status != WorldStatus.APPROVED:
            raise ValueError("Only APPROVED Worlds can be merged")
        source.status = WorldStatus.MERGED
        source.updated_at = datetime.utcnow()
        self._session.add(source)
        self._session.commit()
        self._session.refresh(source)
        return target


def asyncio_run(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)
