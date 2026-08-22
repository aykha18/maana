"""Neo4j graph projection layer."""

from __future__ import annotations

from typing import Any

from maana_api.config import get_settings

settings = get_settings()
_neo4j_driver = None


def get_neo4j_driver():
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import AsyncGraphDatabase
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _neo4j_driver


async def close_neo4j_driver() -> None:
    global _neo4j_driver
    if _neo4j_driver is not None:
        await _neo4j_driver.close()
        _neo4j_driver = None


class GraphProjection:
    """Neo4j projection of governed semantic relationships."""

    def __init__(self) -> None:
        self._driver = get_neo4j_driver()

    async def health_check(self) -> bool:
        try:
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception:
            return False

    async def create_world_node(self, world: Any) -> None:
        query = """
        MERGE (w:World {world_id: $world_id})
        SET w.canonical_term = $canonical_term,
            w.transliteration = $transliteration,
            w.status = $status,
            w.scope = $scope,
            w.updated_at = datetime()
        """
        async with self._driver.session() as session:
            await session.run(
                query,
                {
                    "world_id": world.world_id,
                    "canonical_term": world.canonical_term,
                    "transliteration": world.transliteration,
                    "status": world.status.value,
                    "scope": world.scope.value,
                },
            )

    async def create_relation(self, relation: Any) -> None:
        query = """
        MATCH (source:World {world_id: $source_world_id})
        MATCH (target:World {world_id: $target_world_id})
        MERGE (source)-[r:RELATES_TO {relation_id: $relation_id}]->(target)
        SET r.relation_type = $relation_type,
            r.status = $status,
            r.scope = $scope,
            r.updated_at = datetime()
        """
        async with self._driver.session() as session:
            await session.run(
                query,
                {
                    "relation_id": relation.relation_id,
                    "source_world_id": relation.source_world_id,
                    "target_world_id": relation.target_world_id,
                    "relation_type": relation.relation_type.value,
                    "status": relation.status.value,
                    "scope": relation.scope.value,
                },
            )

    async def delete_world_node(self, world_id: str) -> None:
        query = """
        MATCH (w:World {world_id: $world_id})
        DETACH DELETE w
        """
        async with self._driver.session() as session:
            await session.run(query, {"world_id": world_id})

    async def get_related_worlds(self, world_id: str, depth: int = 1) -> list[dict[str, Any]]:
        query = """
        MATCH (w:World {world_id: $world_id})-[r:RELATES_TO*1..$depth]-(related:World)
        RETURN related, r
        """
        async with self._driver.session() as session:
            result = await session.run(query, {"world_id": world_id, "depth": depth})
            return [record.data() async for record in result]


_graph_projection: GraphProjection | None = None


def get_graph_projection() -> GraphProjection:
    global _graph_projection
    if _graph_projection is None:
        _graph_projection = GraphProjection()
    return _graph_projection
