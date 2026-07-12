"""Path helpers used across pipeline stages."""

from __future__ import annotations

from pathlib import Path

from maana_ingest.config import Settings


def resolve_output_dir(settings: Settings) -> Path:
    """Return the absolute output directory and ensure it exists."""

    output_dir = settings.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
