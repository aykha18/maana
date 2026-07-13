"""Readiness checks and knowledge-manifest bootstrapping for ontology ingestion."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.annotation import AnnotationManifest
from maana_ingest.cleaning.models import CleanedTranscriptDocument
from maana_ingest.config import Settings
from maana_ingest.download import LectureWorkspace
from maana_ingest.ontology.models import ChapterKnowledgeDraft, KnowledgeManifest, ReadinessAssessment
from maana_ingest.ontology.resolver import CanonicalRegistryError, CanonicalRegistryResolver


class OntologyReadinessError(RuntimeError):
    """Raised when ontology readiness cannot be evaluated."""


class OntologyReadinessService:
    """Assess whether a lecture is ready for knowledge-first ingestion."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def assess_lecture(self, lecture_path: Path) -> ReadinessAssessment:
        workspace = self._resolve_workspace(lecture_path)
        registry_loaded = self._load_registry_if_configured() is not None
        artifacts = {
            "source_metadata": workspace.metadata_path.exists(),
            "source_media": workspace.find_raw_media_path() is not None,
            "chapter_manifest": workspace.chapter_manifest_path.exists(),
            "transcription_manifest": workspace.transcription_manifest_path.exists(),
            "cleaned_transcript": workspace.cleaned_transcript_json_path.exists(),
            "annotation_manifest": workspace.annotation_manifest_path.exists(),
            "canonical_registry": registry_loaded,
            "knowledge_manifest": workspace.knowledge_manifest_path.exists(),
        }

        blockers: list[str] = []
        next_tasks: list[str] = []

        if not artifacts["source_metadata"] or not artifacts["source_media"]:
            blockers.append("Source capture is incomplete; download artifacts are missing.")
            next_tasks.append("Run `maana download` and preserve the original lecture artifacts.")

        if not artifacts["chapter_manifest"]:
            blockers.append("Audio segmentation is incomplete; chapter manifest is missing.")
            next_tasks.append("Run `maana split` to normalize audio and create deterministic chapter boundaries.")

        if not artifacts["transcription_manifest"]:
            blockers.append("Speech recognition is incomplete; no transcription manifest exists.")
            next_tasks.append("Run `maana transcribe` to generate chapter transcripts.")

        if not artifacts["cleaned_transcript"]:
            blockers.append("Transcript cleaning is incomplete; ontology extraction should not run on raw ASR.")
            next_tasks.append("Run `maana clean` before attempting knowledge extraction.")

        if not artifacts["annotation_manifest"]:
            blockers.append("Structured annotation is missing; specialized analyzer output is not available.")
            next_tasks.append("Run `maana annotate` to generate structured chapter annotations.")

        if self._settings.annotation_provider.strip().lower() == "mock":
            blockers.append("Annotation provider is still set to `mock`; LLM-backed extraction is not production-ready.")
            next_tasks.append("Configure a live annotation provider before canonical knowledge ingestion.")

        if self._settings.canonical_registry_path is not None and not artifacts["canonical_registry"]:
            blockers.append("Canonical registry is configured but failed validation.")
            next_tasks.append("Fix the canonical registry JSON shape before ontology mapping.")
        elif not artifacts["canonical_registry"]:
            blockers.append("No canonical registry is configured, so new entities cannot be mapped safely.")
            next_tasks.append("Create and configure a canonical registry JSON file before approving ontology entities.")

        curator_ui_ready = False
        blockers.append("Curator UI is not implemented, so approve/reject/merge/split flows are unavailable.")
        next_tasks.append("Build curator review workflows before treating extracted entities as canonical.")

        can_start_artifact_ingestion = all(
            artifacts[name] for name in ("source_metadata", "source_media", "chapter_manifest")
        )
        can_start_knowledge_ingestion = all(
            artifacts[name]
            for name in ("cleaned_transcript", "annotation_manifest", "canonical_registry")
        ) and self._settings.annotation_provider.strip().lower() != "mock" and curator_ui_ready

        summary = (
            "Artifact ingestion can continue, but canonical knowledge ingestion must remain gated."
            if can_start_artifact_ingestion and not can_start_knowledge_ingestion
            else "The lecture is not ready even for artifact ingestion."
            if not can_start_artifact_ingestion
            else "The lecture is ready for canonical knowledge ingestion."
        )

        return ReadinessAssessment(
            lecture_root=workspace.lecture_root.resolve(),
            can_start_artifact_ingestion=can_start_artifact_ingestion,
            can_start_knowledge_ingestion=can_start_knowledge_ingestion,
            curator_ui_ready=curator_ui_ready,
            annotation_provider=self._settings.annotation_provider,
            available_artifacts=artifacts,
            blockers=_unique(blockers),
            next_tasks=_unique(next_tasks),
            summary=summary,
        )

    def initialize_knowledge_manifest(self, lecture_path: Path, *, force: bool = False) -> KnowledgeManifest:
        workspace = self._resolve_workspace(lecture_path)
        workspace.ensure_exists()

        if workspace.knowledge_manifest_path.exists() and not force:
            return KnowledgeManifest.model_validate_json(
                workspace.knowledge_manifest_path.read_text(encoding="utf-8")
            )

        cleaned_document = self._load_cleaned_document(workspace.cleaned_transcript_json_path)
        annotation_manifest = self._load_annotation_manifest(workspace.annotation_manifest_path)
        assessment = self.assess_lecture(workspace.lecture_root)
        annotation_lookup = {
            chapter.chapter_number: chapter.merged_output_path for chapter in annotation_manifest.chapters
        }

        chapters: list[ChapterKnowledgeDraft] = []
        for chapter in cleaned_document.chapters:
            chapter_output_dir = workspace.knowledge_chapters_dir / f"chapter-{chapter.chapter_number:03d}"
            chapter_output_dir.mkdir(parents=True, exist_ok=True)
            blockers = []
            if chapter.chapter_number not in annotation_lookup:
                blockers.append("No merged annotation output exists for this chapter.")

            draft = ChapterKnowledgeDraft(
                chapter_number=chapter.chapter_number,
                source_cleaned_path=workspace.cleaned_transcript_json_path.resolve(),
                source_annotation_path=annotation_lookup.get(chapter.chapter_number),
                blockers=blockers,
            )
            draft_path = chapter_output_dir / "draft.json"
            draft_path.write_text(
                json.dumps(draft.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            chapters.append(draft)

        manifest = KnowledgeManifest(
            lecture_root=workspace.lecture_root.resolve(),
            knowledge_dir=workspace.knowledge_dir.resolve(),
            manifest_path=workspace.knowledge_manifest_path.resolve(),
            total_chapters=len(chapters),
            chapters_pending_review=len(chapters),
            ready_for_canonical_ingestion=False,
            blockers=assessment.blockers,
            chapters=chapters,
        )
        workspace.knowledge_manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return manifest

    @staticmethod
    def _resolve_workspace(lecture_path: Path) -> LectureWorkspace:
        path = lecture_path.expanduser().resolve()
        if path.is_dir():
            if (path / "metadata" / "metadata.json").exists():
                return LectureWorkspace.from_lecture_root(path)
            raise OntologyReadinessError(f"Directory does not look like a lecture workspace: {path}")

        if path.is_file():
            if path.name == "manifest.json" and path.parent.name == "knowledge":
                return LectureWorkspace.from_lecture_root(path.parent.parent)
            raise OntologyReadinessError(
                "File input must point to a lecture knowledge manifest inside the knowledge directory"
            )

        raise OntologyReadinessError(f"Lecture path does not exist: {path}")

    def _load_registry_if_configured(self) -> CanonicalRegistryResolver | None:
        if self._settings.canonical_registry_path is None:
            return None
        try:
            return CanonicalRegistryResolver.from_path(self._settings.canonical_registry_path)
        except CanonicalRegistryError:
            return None

    @staticmethod
    def _load_cleaned_document(path: Path) -> CleanedTranscriptDocument:
        if not path.exists():
            raise OntologyReadinessError(f"Cleaned transcript JSON not found: {path}")
        return CleanedTranscriptDocument.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_annotation_manifest(path: Path) -> AnnotationManifest:
        if not path.exists():
            raise OntologyReadinessError(f"Annotation manifest not found: {path}")
        return AnnotationManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values
