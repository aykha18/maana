"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from maana_api.config import get_settings
from maana_api.infrastructure.database import init_db
from maana_api.api import worlds, claims

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

app.include_router(worlds.router)
app.include_router(claims.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/ready")
def ready() -> dict[str, bool]:
    return {"ready": True}
