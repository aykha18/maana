"""Logging helpers for the CLI and pipeline."""

from __future__ import annotations

import sys

from loguru import logger


def configure_logging(verbose: bool = False) -> None:
    """Configure console logging for the ingestion app."""

    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
