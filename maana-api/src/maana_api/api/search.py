"""Global search API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from maana_api.config import get_settings
from maana_api.infrastructure.database import get_db_session
from maana_api.infrastructure.vector_store import get_vector_store
from maana_api.services.world_service import WorldService
from maana_api.services.claim_service import ClaimService

settings = get_settings()
router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
def global_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_db_session),
) -> dict[str, list]:
    """Global search across Worlds, Claims, and other entities."""
    world_service = WorldService(session=session)
    claim_service = ClaimService(session=session)

    worlds = world_service.list_worlds()
    claims = claim_service.list_claims()

    # Simple in-memory search (in production, use PostgreSQL full-text search or Elasticsearch)
    world_results = [w for w in worlds if q.lower() in w.canonical_term.lower() or (w.english_gloss and q.lower() in w.english_gloss.lower())]
    claim_results = [c for c in claims if q.lower() in c.text.lower()]

    return {
        "worlds": world_results[:limit],
        "claims": claim_results[:limit],
    }


@router.get("/semantic")
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    embedding_type: str = Query("world_definition", description="Embedding type to search"),
    model_version: str | None = Query(None, description="Model version"),
    scope: str | None = Query(None, description="Scope filter"),
    session: Session = Depends(get_db_session),
) -> dict[str, list]:
    """Semantic search using vector embeddings."""
    vector_store = get_vector_store(session)
    
    # In production, this would use an embedding model to convert q to vector
    # For now, return empty results as placeholder
    results = await vector_store.query(
        vector=[0.0] * settings.embedding_dimensions,  # placeholder
        limit=limit,
        embedding_type=embedding_type,
        model_version=model_version,
        scope=scope,
    )
    
    return {"results": results}