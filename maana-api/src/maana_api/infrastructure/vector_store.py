"""pgvector-backed VectorStore implementation."""

from __future__ import annotations

from typing import Any, Protocol

from maana_api.config import get_settings
from maana_api.domain.models import EmbeddingProvenance

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
        raise NotImplementedError("PgVectorStore.upsert not yet implemented")

    async def query(
        self,
        vector: list[float],
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        embedding_type: str | None = None,
        model_version: str | None = None,
        scope: str | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("PgVectorStore.query not yet implemented")

    async def delete(self, entity_id: str) -> None:
        raise NotImplementedError("PgVectorStore.delete not yet implemented")

    async def reindex(self, from_model: str, to_model: str) -> None:
        raise NotImplementedError("PgVectorStore.reindex not yet implemented")

    async def health_check(self) -> bool:
        return True

    async def get_by_entity(self, entity_id: str) -> list[dict[str, Any]] | None:
        raise NotImplementedError("PgVectorStore.get_by_entity not yet implemented")

    async def count(self) -> int:
        raise NotImplementedError("PgVectorStore.count not yet implemented")

    async def get_model_info(self) -> dict[str, Any]:
        return {
            "model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions,
            "backend": "pgvector",
        }


def get_vector_store(session) -> PgVectorStore:
    return PgVectorStore(session=session)
