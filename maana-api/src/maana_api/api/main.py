"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from maana_api.config import get_settings
from maana_api.infrastructure.database import init_db
from maana_api.api import worlds, claims, relations, paths, search, agents, challenges
from maana_api.services.validation import InvariantViolation

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Ma'na semantic infrastructure API")
    init_db()
    yield
    logger.info("Shutting down Ma'na semantic infrastructure API")


app = FastAPI(
    title="Ma'na API",
    description="Semantic infrastructure API for governed knowledge, World engine, agents, and retrieval.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(InvariantViolation)
async def invariant_violation_handler(
    request: Request, exc: InvariantViolation
) -> JSONResponse:
    """Report an ontology invariant violation as a client error, not a 500.

    A rejected write is a request that cannot be satisfied as written, so it is
    a 422 with the violated invariant named. Surfacing these as server errors
    would hide a modelling problem behind an infrastructure fault.
    """

    logger.warning(
        "Ontology invariant {invariant} violated on {path}: {detail}",
        invariant=exc.invariant,
        path=request.url.path,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "invariant": exc.invariant},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Lifecycle and state-transition rejections are client errors too."""

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )

app.include_router(worlds.router)
app.include_router(claims.router)
app.include_router(relations.router)
app.include_router(paths.router)
app.include_router(search.router)
app.include_router(agents.router)
app.include_router(challenges.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/ready")
def ready() -> dict[str, bool]:
    return {"ready": True}
