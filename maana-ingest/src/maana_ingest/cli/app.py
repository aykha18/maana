"""CLI entrypoint for Maana ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from maana_ingest.annotation import AnnotationError, AnnotationService
from maana_ingest.audio import AudioPreparationError, AudioPreparationService
from maana_ingest.cleaning import TranscriptCleaningError, TranscriptCleaningService
from maana_ingest.config import get_settings
from maana_ingest.core import configure_logging, resolve_output_dir
from maana_ingest.download import DownloadStageError, YtDlpDownloadService
from maana_ingest.exporters import (
    CommentaryExportService,
    CommentaryJsonExporter,
    CommentaryMarkdownExporter,
)
from maana_ingest.models import SourceRequest, SourceType
from maana_ingest.ontology import (
    LectureCuratorReviewError,
    LectureCuratorReviewService,
    LectureCommentaryComposer,
    LectureCommentaryError,
    OntologyReadinessError,
    OntologyReadinessService,
)
from maana_ingest.poems import (
    PoemCuratorReviewError,
    PoemCuratorReviewService,
    PoemDatasetResolutionService,
    PoemResolutionError,
    ReviewedPoemDatasetService,
    ReviewedPoemMaterializationError,
)
from maana_ingest.speech import SpeechRecognitionError, SpeechRecognitionService

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


def _normalize_commentary_export_formats(formats: Optional[list[str]] = None) -> list[str]:
    requested_formats = formats or ["json", "markdown"]
    normalized_formats = list(dict.fromkeys(format_name.strip().lower() for format_name in requested_formats))
    for format_name in normalized_formats:
        if format_name not in {"json", "markdown"}:
            raise typer.BadParameter(
                f"Unsupported commentary export format: {format_name}. Use 'json' and/or 'markdown'."
            )
    return normalized_formats


def _build_commentary_export_service(formats: Optional[list[str]] = None) -> CommentaryExportService:
    normalized_formats = _normalize_commentary_export_formats(formats)
    exporters = []
    for format_name in normalized_formats:
        if format_name == "json":
            exporters.append(CommentaryJsonExporter())
        elif format_name == "markdown":
            exporters.append(CommentaryMarkdownExporter())
    return CommentaryExportService(exporters=exporters)


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
def split(
    lecture_path: Path,
    trim_silence: Optional[bool] = typer.Option(
        None,
        "--trim-silence/--no-trim-silence",
        help="Override silence trimming for normalization.",
    ),
    segment_length: Optional[int] = typer.Option(
        None,
        "--segment-length",
        help="Override chapter segment length in seconds.",
    ),
) -> None:
    """Normalize source audio and split it into chapter files."""

    settings = get_settings()
    service = AudioPreparationService(settings=settings)
    try:
        result = service.prepare_audio(
            lecture_path,
            trim_silence=trim_silence,
            segment_length=segment_length,
        )
    except AudioPreparationError as exc:
        logger.error("Audio preparation failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Source media: {result.source_media_path}")
    typer.echo(f"Normalized audio: {result.normalized_audio_path}")
    typer.echo(f"Chapter manifest: {result.chapter_manifest_path}")
    typer.echo(f"Chapter count: {len(result.chapters)}")


@app.command()
def transcribe(
    lecture_path: Path,
    language: Optional[str] = typer.Option(
        None,
        "--language",
        help="Optional language hint passed to the whisper model.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Rebuild transcript outputs even if chapter files already exist.",
    ),
) -> None:
    """Transcribe prepared chapter audio into JSON, text, SRT, and VTT outputs."""

    settings = get_settings()
    service = SpeechRecognitionService(settings=settings)
    try:
        result = service.transcribe_lecture(
            lecture_path,
            language=language,
            force=force,
            progress_callback=typer.echo,
        )
    except SpeechRecognitionError as exc:
        logger.error("Transcription failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Transcription manifest: {result.transcription_manifest_path}")
    typer.echo(f"Model: {result.model_name}")
    typer.echo(f"Device: {result.device}")
    typer.echo(f"Compute type: {result.compute_type}")
    typer.echo(f"Completed chapters: {result.completed_chapters}")
    typer.echo(f"Skipped chapters: {result.skipped_chapters}")


@app.command()
def annotate(
    lecture_path: Path,
    force: bool = typer.Option(
        False,
        "--force",
        help="Rebuild annotation outputs even if they already exist.",
    ),
) -> None:
    """Run specialized analyzers over cleaned transcript chapters."""

    settings = get_settings()
    service = AnnotationService(settings=settings)
    try:
        result = service.annotate_lecture(
            lecture_path,
            force=force,
            progress_callback=typer.echo,
        )
    except AnnotationError as exc:
        logger.error("Annotation failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Annotation manifest: {result.annotation_manifest_path}")
    typer.echo(f"Provider: {result.provider}")
    typer.echo(f"Model: {result.model_name}")
    typer.echo(f"Prompt version: {result.prompt_version}")
    typer.echo(f"Completed chapters: {result.completed_chapters}")
    typer.echo(f"Skipped chapters: {result.skipped_chapters}")
    typer.echo(f"Chapter count: {result.chapter_count}")


@app.command()
def clean(
    lecture_path: Path,
    force: bool = typer.Option(
        False,
        "--force",
        help="Rebuild cleaned outputs even if they already exist.",
    ),
) -> None:
    """Clean raw ASR transcript outputs into timestamp-aware lecture documents."""

    settings = get_settings()
    service = TranscriptCleaningService(settings=settings)
    try:
        result = service.clean_transcripts(lecture_path, force=force)
    except TranscriptCleaningError as exc:
        logger.error("Transcript cleaning failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Clean JSON: {result.cleaned_json_path}")
    typer.echo(f"Clean Markdown: {result.cleaned_markdown_path}")
    typer.echo(f"Total chapters: {result.total_chapters}")
    typer.echo(f"Total segments: {result.total_segments}")
    typer.echo(f"Merged segments: {result.merged_segment_count}")


@app.command()
def process(url: str, output_dir: Optional[Path] = None) -> None:
    """Placeholder command for the end-to-end pipeline."""

    logger.info("Process stage scaffolded for {}", url)
    if output_dir is not None:
        typer.echo(f"Requested output directory: {output_dir}")
    typer.echo(f"Process stage scaffolded for: {url}")


@app.command()
def assess(
    lecture_path: Path,
    prepare_knowledge_manifest: bool = typer.Option(
        False,
        "--prepare-knowledge-manifest",
        help="Bootstrap a Phase 6 knowledge manifest if cleaned and annotated artifacts already exist.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Rebuild the knowledge manifest even if it already exists.",
    ),
) -> None:
    """Assess whether a lecture is ready for knowledge-first ingestion."""

    settings = get_settings()
    service = OntologyReadinessService(settings=settings)
    try:
        assessment = service.assess_lecture(lecture_path)
        manifest = None
        if prepare_knowledge_manifest:
            manifest = service.initialize_knowledge_manifest(lecture_path, force=force)
    except OntologyReadinessError as exc:
        logger.error("Ontology readiness assessment failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {assessment.lecture_root}")
    typer.echo(f"Artifact ingestion ready: {assessment.can_start_artifact_ingestion}")
    typer.echo(f"Knowledge ingestion ready: {assessment.can_start_knowledge_ingestion}")
    typer.echo(f"Curator UI ready: {assessment.curator_ui_ready}")
    typer.echo(f"Annotation provider: {assessment.annotation_provider}")
    typer.echo(f"Summary: {assessment.summary}")
    typer.echo("Artifacts:")
    for name, available in assessment.available_artifacts.items():
        typer.echo(f"- {name}: {available}")
    if assessment.blockers:
        typer.echo("Blockers:")
        for blocker in assessment.blockers:
            typer.echo(f"- {blocker}")
    if assessment.next_tasks:
        typer.echo("Next tasks:")
        for task in assessment.next_tasks:
            typer.echo(f"- {task}")
    if manifest is not None:
        typer.echo(f"Knowledge manifest: {manifest.manifest_path}")
        typer.echo(f"Knowledge chapters pending review: {manifest.chapters_pending_review}")


@app.command("prepare-lecture-review")
def prepare_lecture_review(
    knowledge_manifest_path: Path,
    output_path: Optional[Path] = typer.Option(
        None,
        "--output-path",
        "-o",
        help="Optional path for the generated lecture claim review JSON file.",
    ),
) -> None:
    """Prepare a curator review queue from lecture claim bundles."""

    settings = get_settings()
    service = LectureCuratorReviewService(settings=settings)
    try:
        result = service.generate_review_file(knowledge_manifest_path, output_path=output_path)
    except LectureCuratorReviewError as exc:
        logger.error("Lecture review preparation failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Review path: {result.review_path}")
    typer.echo(f"Total items: {result.total_items}")
    typer.echo(f"Pending items: {result.pending_items}")


@app.command("apply-lecture-review")
def apply_lecture_review(review_path: Path) -> None:
    """Apply curator decisions to lecture claim bundles and ontology candidates."""

    settings = get_settings()
    service = LectureCuratorReviewService(settings=settings)
    try:
        result = service.apply_review_file(review_path)
    except LectureCuratorReviewError as exc:
        logger.error("Applying lecture review failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Review path: {result.review_path}")
    typer.echo(f"Applied path: {result.applied_path}")
    typer.echo(f"Registry path: {result.registry_path}")
    typer.echo(f"Approved claims: {result.approved_claims}")
    typer.echo(f"Rejected claims: {result.rejected_claims}")
    typer.echo(f"Revision requested: {result.revision_requested_claims}")
    typer.echo(f"Pending claims: {result.pending_claims}")
    typer.echo(f"Ontology appended entries: {result.ontology_appended_entries}")
    typer.echo(f"Ontology approved existing: {result.ontology_approved_existing}")
    typer.echo(f"Ontology rejected: {result.ontology_rejected}")


@app.command("compose-lecture-commentary")
def compose_lecture_commentary(
    knowledge_manifest_path: Path,
    force: bool = typer.Option(
        False,
        "--force",
        help="Rebuild commentary artifacts even if they already exist.",
    ),
    formats: Optional[list[str]] = typer.Option(
        None,
        "--format",
        "-f",
        help="Repeatable commentary export format. Supported values: json, markdown.",
    ),
) -> None:
    """Compose per-chapter commentary artifacts from approved lecture claim bundles."""

    settings = get_settings()
    normalized_formats = _normalize_commentary_export_formats(formats)
    export_service = _build_commentary_export_service(normalized_formats)
    service = LectureCommentaryComposer(settings=settings, export_service=export_service)
    try:
        result = service.compose_from_manifest(knowledge_manifest_path, force=force)
    except LectureCommentaryError as exc:
        logger.error("Commentary composition failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Lecture workspace: {result.lecture_root}")
    typer.echo(f"Knowledge manifest: {result.knowledge_manifest_path}")
    typer.echo(f"Export formats: {', '.join(normalized_formats)}")
    typer.echo(f"Composed chapters: {result.composed_chapters}")
    typer.echo(f"Skipped chapters: {result.skipped_chapters}")
    if result.chapter_artifacts:
        typer.echo("Artifacts:")
        for artifact in result.chapter_artifacts:
            typer.echo(f"- {artifact}")


@app.command("resolve-poem-dataset")
def resolve_poem_dataset(
    dataset_path: Path,
    output_path: Optional[Path] = typer.Option(
        None,
        "--output-path",
        "-o",
        help="Optional path for the resolved dataset JSON output.",
    ),
) -> None:
    """Resolve a structured poem dataset against the canonical registry."""

    settings = get_settings()
    service = PoemDatasetResolutionService(settings=settings)
    try:
        result = service.resolve_dataset(dataset_path, output_path=output_path)
    except PoemResolutionError as exc:
        logger.error("Poem dataset resolution failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Dataset: {result.dataset_name}")
    typer.echo(f"Input path: {result.input_path}")
    typer.echo(f"Output path: {result.output_path}")
    typer.echo(f"Total poems: {result.total_poems}")
    typer.echo(f"Total resolutions: {result.total_resolutions}")
    typer.echo(f"Matched resolutions: {result.matched_resolutions}")
    typer.echo(f"Proposed new resolutions: {result.proposed_new_resolutions}")


@app.command("prepare-poem-review")
def prepare_poem_review(
    resolved_dataset_path: Path,
    output_path: Optional[Path] = typer.Option(
        None,
        "--output-path",
        "-o",
        help="Optional path for the generated curator review JSON file.",
    ),
) -> None:
    """Prepare a curator review queue from unresolved poem ontology resolutions."""

    settings = get_settings()
    service = PoemCuratorReviewService(settings=settings)
    try:
        review_file = service.generate_review_file(resolved_dataset_path, output_path=output_path)
    except PoemCuratorReviewError as exc:
        logger.error("Poem review preparation failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Dataset: {review_file.dataset_name}")
    typer.echo(f"Resolved dataset: {review_file.resolved_dataset_path}")
    typer.echo(f"Review path: {review_file.review_path}")
    typer.echo(f"Total candidates: {review_file.total_candidates}")
    typer.echo(f"Pending candidates: {review_file.pending_candidates}")


@app.command("append-approved-terms")
def append_approved_terms(review_path: Path) -> None:
    """Append curator-approved new ontology terms into the canonical registry."""

    settings = get_settings()
    service = PoemCuratorReviewService(settings=settings)
    try:
        result = service.append_approved_terms(review_path)
    except PoemCuratorReviewError as exc:
        logger.error("Appending approved terms failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Review path: {result.review_path}")
    typer.echo(f"Registry path: {result.registry_path}")
    typer.echo(f"Applied path: {result.applied_path}")
    typer.echo(f"Appended entries: {result.appended_entries}")
    typer.echo(f"Skipped existing: {result.skipped_existing}")
    typer.echo(f"Approved existing: {result.approved_existing}")
    typer.echo(f"Pending or rejected: {result.pending_or_rejected}")


@app.command("materialize-reviewed-poem-dataset")
def materialize_reviewed_poem_dataset(
    applied_review_path: Path,
    output_path: Optional[Path] = typer.Option(
        None,
        "--output-path",
        "-o",
        help="Optional path for the final reviewed poem dataset JSON.",
    ),
) -> None:
    """Materialize the final reviewed poem dataset from applied curator decisions."""

    settings = get_settings()
    service = ReviewedPoemDatasetService(settings=settings)
    try:
        result = service.materialize_from_applied_review(
            applied_review_path,
            output_path=output_path,
        )
    except ReviewedPoemMaterializationError as exc:
        logger.error("Reviewed poem dataset materialization failed: {}", exc)
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Dataset: {result.dataset_name}")
    typer.echo(f"Output path: {result.output_path}")
    typer.echo(f"Total poems: {result.total_poems}")
    typer.echo(f"Fully reviewed poems: {result.fully_reviewed_poems}")


def main() -> None:
    """Script entrypoint used by `python -m` and project scripts."""

    app()
