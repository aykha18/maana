"""Specialized annotation orchestration over cleaned transcript outputs."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.annotation.citation_resolver import CitationResolver
from maana_ingest.annotation.client import AnnotationClientError, AnnotationClientFactory, AnnotationLLMClient
from maana_ingest.annotation.couplet_detector import CoupletDetector
from maana_ingest.annotation.hadith_detector import HadithDetector
from maana_ingest.annotation.interpretation_hints import enrich_merged_annotation
from maana_ingest.annotation.merger import merge_chapter_annotations
from maana_ingest.annotation.models import (
    AnnotationManifest,
    AnnotationResult,
    MergedChapterAnnotation,
)
from maana_ingest.annotation.persian_detector import PersianDetector
from maana_ingest.annotation.poet_detector import PoetDetector
from maana_ingest.annotation.quran_detector import QuranDetector
from maana_ingest.cleaning.models import CleanedChapterTranscript, CleanedTranscriptDocument
from maana_ingest.config import Settings
from maana_ingest.download import LectureWorkspace


class AnnotationError(RuntimeError):
    """Raised when annotation cannot proceed."""


class AnnotationService:
    """Run specialized analyzers over cleaned transcript chapters."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: AnnotationLLMClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client
        self._analyzers = [
            CoupletDetector(),
            QuranDetector(),
            HadithDetector(),
            PoetDetector(),
            PersianDetector(),
            CitationResolver(),
        ]

    def annotate_lecture(
        self,
        lecture_path: Path,
        *,
        force: bool = False,
        progress_callback: callable | None = None,
    ) -> AnnotationResult:
        workspace = self._resolve_workspace(lecture_path)
        workspace.ensure_exists()
        cleaned_document = self._load_cleaned_document(workspace.cleaned_transcript_json_path)
        if not cleaned_document.chapters:
            raise AnnotationError("Cleaned transcript document contains no chapters to annotate")

        try:
            client = self._client or AnnotationClientFactory.from_settings(self._settings)
        except AnnotationClientError as exc:
            raise AnnotationError(str(exc)) from exc

        merged_chapters: list[MergedChapterAnnotation] = []
        completed = 0
        skipped = 0

        for chapter in cleaned_document.chapters:
            chapter_dir = workspace.annotation_chapters_dir / f"chapter-{chapter.chapter_number:03d}"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            merged_output_path = chapter_dir / "merged.json"

            if not force and merged_output_path.exists():
                merged_chapters.append(
                    MergedChapterAnnotation.model_validate_json(
                        merged_output_path.read_text(encoding="utf-8")
                    )
                )
                skipped += 1
                if progress_callback is not None:
                    progress_callback(f"Skipped chapter {chapter.chapter_number}: merged annotation already exists")
                continue

            if progress_callback is not None:
                progress_callback(
                    f"Annotating chapter {chapter.chapter_number}/{len(cleaned_document.chapters)}"
                )

            analyzer_results = {}
            analyzer_executions = []
            for analyzer in self._analyzers:
                result, execution = analyzer.analyze(
                    chapter=chapter,
                    chapter_output_dir=chapter_dir,
                    client=client,
                    prompt_version=self._settings.annotation_prompt_version,
                    force=force,
                )
                analyzer_results[analyzer.name] = result
                analyzer_executions.append(execution)

            merged = merge_chapter_annotations(
                chapter_number=chapter.chapter_number,
                source_cleaned_path=workspace.cleaned_transcript_json_path,
                merged_output_path=merged_output_path,
                analyzers=analyzer_executions,
                couplets=analyzer_results["couplet_detector"],
                quran=analyzer_results["quran_detector"],
                hadith=analyzer_results["hadith_detector"],
                poets=analyzer_results["poet_detector"],
                persian=analyzer_results["persian_detector"],
                citations=analyzer_results["citation_resolver"],
            )
            merged = enrich_merged_annotation(merged)
            merged_output_path.write_text(
                json.dumps(merged.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            merged_chapters.append(merged)
            completed += 1

        manifest = AnnotationManifest(
            lecture_root=workspace.lecture_root.resolve(),
            annotation_dir=workspace.annotation_dir.resolve(),
            provider=client.provider_name,
            model_name=client.model_name,
            prompt_version=self._settings.annotation_prompt_version,
            completed_chapters=completed,
            skipped_chapters=skipped,
            chapters=merged_chapters,
        )
        workspace.annotation_manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return AnnotationResult(
            lecture_root=workspace.lecture_root.resolve(),
            annotation_manifest_path=workspace.annotation_manifest_path.resolve(),
            provider=client.provider_name,
            model_name=client.model_name,
            prompt_version=self._settings.annotation_prompt_version,
            completed_chapters=completed,
            skipped_chapters=skipped,
            chapter_count=len(merged_chapters),
        )

    @staticmethod
    def _resolve_workspace(lecture_path: Path) -> LectureWorkspace:
        path = lecture_path.expanduser().resolve()
        if path.is_dir():
            if (path / "cleaned" / "transcript.json").exists():
                return LectureWorkspace.from_lecture_root(path)
            raise AnnotationError(f"Directory does not look like a cleaned lecture workspace: {path}")

        if path.is_file():
            if path.name == "transcript.json" and path.parent.name == "cleaned":
                return LectureWorkspace.from_lecture_root(path.parent.parent)
            raise AnnotationError(
                "File input must point to the cleaned transcript JSON inside the cleaned directory"
            )

        raise AnnotationError(f"Lecture path does not exist: {path}")

    @staticmethod
    def _load_cleaned_document(path: Path) -> CleanedTranscriptDocument:
        if not path.exists():
            raise AnnotationError(f"Cleaned transcript JSON not found: {path}")
        return CleanedTranscriptDocument.model_validate_json(path.read_text(encoding="utf-8"))
