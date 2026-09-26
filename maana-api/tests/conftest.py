"""Shared test fixtures.

The graph is a projection of PostgreSQL, never a source of truth (Ontology
I-076). Tests must not depend on a running Neo4j: without a mock, every
approval attempts a real connection and the suite spends its time in
connection timeouts.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import SQLModel, Session, create_engine

from maana_api.infrastructure.projection import clear_failures, pending_failures


@pytest.fixture(autouse=True)
def _mock_graph_projection():
    """Replace the Neo4j projection in both services with an async mock."""

    mock_graph = MagicMock()
    mock_graph.create_world_node = AsyncMock()
    mock_graph.create_relation = AsyncMock()
    mock_graph.delete_world_node = AsyncMock()
    mock_graph.get_related_worlds = AsyncMock(return_value=[])
    mock_graph.health_check = AsyncMock(return_value=True)

    with patch(
        "maana_api.services.world_service.get_graph_projection",
        return_value=mock_graph,
    ), patch(
        "maana_api.services.relation_service.get_graph_projection",
        return_value=mock_graph,
    ):
        yield mock_graph


@pytest.fixture(autouse=True)
def _clear_projection_failures():
    """No projection failure may leak between tests."""

    clear_failures()
    yield
    clear_failures()


@pytest.fixture
def engine():
    """An isolated in-memory database with the full schema."""

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Session:
    with Session(engine) as session:
        yield session
