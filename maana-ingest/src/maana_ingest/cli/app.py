"""CLI entrypoint for Maana ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from maana_ingest.config import get_settings
from maana_ingest.core import configure_logging, resolve_output_dir
from maana_ingest.download import DownloadStageError, YtDlpDownloadService
from maana_ingest.models import SourceRequest, SourceType

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


def _create_download_request(
    url: str,
    output_dir: Path | None,
    source_type: SourceType,
) -> SourceRequest:
    settings = get_settings()
    resolved_output_dir = output_dir or resolve_output_dir(settings)
    return SourceRequest(
        url=url,
        source_type=source_type,
        output_dir=resolved_output_dir,
    )


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging."),
) -> None:
    """Set up logging and shared runtime configuration."""

    _bootstrap(verbose=verbose)


@app.command()
def download(
    url: str,
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Override the configured output directory.",
    ),
    source_type: SourceType = typer.Option(
        SourceType.YOUTUBE,
        "--source-type",
        help="Source type to ingest.",
    ),
) -> None:
    """Download a source lecture and persist metadata plus media artifacts."""

    settings = get_settings()
    request = _create_download_request(url, output_dir, source_type)
    service = YtDlpDownloadService(settings=settings)

    try:
        result = service.download(request)
    except DownloadStageError as exc:
        logger.error("Download failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Source directory: {result.source_dir}")
    typer.echo(f"Metadata JSON: {result.metadata_path}")
    if result.raw_media_path is not None:
        typer.echo(f"Source media: {result.raw_media_path}")
    typer.echo(f"Skipped existing download: {result.skipped}")


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
