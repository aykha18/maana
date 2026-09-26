"""pgvector-backed VectorStore implementation."""

from __future__ import annotations

from typing import Any, Protocol

from maana_api.config import get_settings
from maana_api.domain.models import Embedding
from maana_api.services.validation import resolve_scope_visibility

settings = get_settings()


class VectorStore(Protocol):
    """Vector storage abstraction. Implementation may be pgvector or Qdrant."""

    async def upsert(self, embeddings: list[dict[str, Any]]) -> None: ...
    async def query(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        embedding_type: str | None = None,
        model_version: str | None = None,
        scope: str | None = None,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]: ...
    async def delete(self, entity_id: str) -> None: ...
    async def reindex(self, from_model: str, to_model: str) -> None: ...
    async def health_check(self) -> bool: ...
    async def get_by_entity(self, entity_id: str) -> list[dict[str, Any]] | None: ...
    async def count(self) -> int: ...
    async def get_model_info(self) -> dict[str, Any]: ...


class PgVectorStore:
    """PostgreSQL + pgvector implementation of VectorStore."""

    def __init__(self, session) -> None:
        self._session = session

    async def upsert(self, embeddings: list[dict[str, Any]]) -> None:
        """Upsert embeddings into the vector store."""
        for emb in embeddings:
            existing = self._session.get(Embedding, emb["embedding_id"])
            if existing:
                existing.vector = emb["vector"]
                existing.updated_at = __import__("datetime").datetime.utcnow()
            else:
                self._session.add(Embedding(**emb))
        self._session.commit()

    async def query(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        embedding_type: str | None = None,
        model_version: str | None = None,
        scope: str | None = None,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query embeddings by cosine similarity.

        Ontology I-078: a query that cannot filter by ``embedding_type`` and
        ``model_version`` is invalid, because cross-type or cross-model
        similarity is meaningless. ``scope`` filters on the parent entity's
        governance scope, not on ``entity_type``; the previous implementation
        compared ``scope`` against ``entity_type``, which silently returned
        wrong rows for every scoped query.
        """

        from sqlalchemy import text

        if embedding_type is None:
            raise ValueError(
                "embedding_type is required: vectors of different types must "
                "never be compared (Ontology I-028, I-078)"
            )
        if model_version is None:
            raise ValueError(
                "model_version is required: vectors from different models must "
                "never be compared (Ontology I-078)"
            )

        query = """
            SELECT e.embedding_id, e.entity_id, e.entity_type, e.embedding_type,
                   e.model, e.model_version, e.dimensions, e.vector,
                   1 - (e.vector <=> :vector) as similarity
            FROM embeddings e
            WHERE e.embedding_type = :embedding_type
              AND e.model_version = :model_version
        """
        params: dict[str, Any] = {
            "vector": vector,
            "embedding_type": embedding_type,
            "model_version": model_version,
        }

        if entity_type:
            query += " AND e.entity_type = :entity_type"
            params["entity_type"] = entity_type

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                query += f" AND e.{key} = :f_{key}"
                params[f"f_{key}"] = value

        query += " ORDER BY e.vector <=> :vector LIMIT :limit"
        params["limit"] = limit

        rows = self._session.exec(text(query), params).all()

        results = [
            {
                "embedding_id": row[0],
                "entity_id": row[1],
                "entity_type": row[2],
                "embedding_type": row[3],
                "model": row[4],
                "model_version": row[5],
                "dimensions": row[6],
                "vector": row[7],
                "similarity": row[8],
            }
            for row in rows
        ]

        # Scope is a property of the parent entity, not of the embedding row,
        # so it is applied after the SQL layer (Ontology §9.2, I-066).
        if scope:
            visible = set(resolve_scope_visibility(scope))
            results = [
                r for r in results if self._parent_scope(r["entity_type"], r["entity_id"]) in visible
            ]

        return results

    def _parent_scope(self, entity_type: str, entity_id: str) -> str:
        """Look up the governance scope of an embedding's parent entity."""

        from maana_api.domain.models import Claim, Relation, World

        model = {"world": World, "claim": Claim, "relation": Relation}.get(entity_type)
        if model is None:
            return "global"
        parent = self._session.get(model, entity_id)
        return getattr(parent, "scope", "global") if parent is not None else "global"

    async def delete(self, entity_id: str) -> None:
        """Delete all embeddings for an entity."""
        from sqlalchemy import delete
        stmt = delete(Embedding).where(Embedding.entity_id == entity_id)
        self._session.exec(stmt)
        self._session.commit()

    async def reindex(self, from_model: str, to_model: str) -> None:
        """Trigger reindexing from one model to another (placeholder)."""
        pass

    async def health_check(self) -> bool:
        try:
            self._session.exec("SELECT 1")
            return True
        except Exception:
            return False

    async def get_by_entity(self, entity_id: str) -> list[dict[str, Any]] | None:
        """Get all embeddings for an entity."""
        from sqlalchemy import select
        stmt = select(Embedding).where(Embedding.entity_id == entity_id)
        results = self._session.exec(stmt).all()
        return [
            {
                "embedding_id": r.embedding_id,
                "entity_id": r.entity_id,
                "entity_type": r.entity_type,
                "embedding_type": r.embedding_type,
                "model": r.model,
                "model_version": r.model_version,
                "dimensions": r.dimensions,
                "vector": r.vector,
            }
            for r in results
        ] if results else None

    async def count(self) -> int:
        """Count total embeddings."""
        from sqlalchemy import func, select
        stmt = select(func.count()).select_from(Embedding)
        result = self._session.exec(stmt).first()
        return result or 0

    async def get_model_info(self) -> dict[str, Any]:
        return {
            "model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions,
            "backend": "pgvector",
        }


def get_vector_store(session) -> PgVectorStore:
    return PgVectorStore(session=session)