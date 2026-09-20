"""pgvector-backed VectorStore implementation."""

from __future__ import annotations

from typing import Any, Protocol

from maana_api.config import get_settings
from maana_api.domain.models import Embedding

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
    ) -> list[dict[str, Any]]:
        """Query embeddings by cosine similarity."""
        from sqlalchemy import text
        
        # Build the query with filters
        query = """
            SELECT embedding_id, entity_id, entity_type, embedding_type, 
                   model, model_version, dimensions, vector,
                   1 - (vector <=> :vector) as similarity
            FROM embeddings
            WHERE 1=1
        """
        params = {"vector": vector}
        
        if embedding_type:
            query += " AND embedding_type = :embedding_type"
            params["embedding_type"] = embedding_type
        if model_version:
            query += " AND model_version = :model_version"
            params["model_version"] = model_version
        if scope:
            query += " AND entity_type = :scope"
            params["scope"] = scope
        
        query += " ORDER BY vector <=> :vector LIMIT :limit"
        params["limit"] = limit
        
        result = self._session.exec(text(query), params).all()
        
        return [
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
            for row in result
        ]

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