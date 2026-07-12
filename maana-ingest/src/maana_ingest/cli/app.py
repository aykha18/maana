"""CLI entrypoint for Maana ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from maana_ingest.config import get_settings
from maana_ingest.core import configure_logging, resolve_output_dir

app = typer.Typer(
    help="Maana ingestion pipeline CLI.",
    no_args_is_help=True,
    add_completion=False,
)


def _bootstrap(verbose: bool = False) -> Path:
    configure_logging(verbose=verbose)
    settings = get_settings()
    output_dir = resolve_output_dir(settings)
    logger.debug(
        "Loaded settings with whisper_model={} segment_length={} output_dir={}",
        settings.whisper_model,
        settings.segment_length,
        output_dir,
    )
    return output_dir


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging."),
) -> None:
    """Set up logging and shared runtime configuration."""

    _bootstrap(verbose=verbose)


@app.command()
def download(url: str) -> None:
    """Placeholder command for source intake and download."""

    logger.info("Download stage scaffolded for {}", url)
    typer.echo(f"Download stage scaffolded for: {url}")


@app.command()
def split(lecture_path: Path) -> None:
    """Placeholder command for audio segmentation."""

    logger.info("Split stage scaffolded for {}", lecture_path)
    typer.echo(f"Split stage scaffolded for: {lecture_path}")


@app.command()
def transcribe(lecture_path: Path) -> None:
    """Placeholder command for speech recognition."""

    logger.info("Transcribe stage scaffolded for {}", lecture_path)
    typer.echo(f"Transcribe stage scaffolded for: {lecture_path}")


@app.command()
def process(url: str, output_dir: Optional[Path] = None) -> None:
    """Placeholder command for the end-to-end pipeline."""

    logger.info("Process stage scaffolded for {}", url)
    if output_dir is not None:
        typer.echo(f"Requested output directory: {output_dir}")
    typer.echo(f"Process stage scaffolded for: {url}")


def main() -> None:
    """Script entrypoint used by `python -m` and project scripts."""

    app()
