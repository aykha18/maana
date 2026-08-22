"""Infrastructure layer: database, vector store, graph projection."""

from __future__ import annotations

from typing import Any, Protocol

from maana_api.config import get_settings

settings = get_settings()

from maana_api.infrastructure.database import (
    DATABASE_URL,
    get_async_engine,
    get_db_session,
    get_sync_engine,
    init_db,
)
from maana_api.infrastructure.vector_store import PgVectorStore, VectorStore, get_vector_store
from maana_api.infrastructure.graph import GraphProjection, get_graph_projection
