"""Resolver-backed poem pilot dataset processing."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.config import Settings
from maana_ingest.ontology import CanonicalEntityType, CanonicalRegistryError, CanonicalRegistryResolver
from maana_ingest.poems.models import (
    PoemPilotDataset,
    PoemResolutionDataset,
    PoemResolutionResult,
    ResolvedOntologyTags,
    ResolvedPoemRecord,
)


class PoemResolutionError(RuntimeError):
    """Raised when a poem pilot dataset cannot be resolved."""


class PoemDatasetResolutionService:
    """Resolve structured poem metadata and ontology tags against the canonical registry."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def resolve_dataset(self, dataset_path: Path, *, output_path: Path | None = None) -> PoemResolutionResult:
        if self._settings.canonical_registry_path is None:
            raise PoemResolutionError("CANONICAL_REGISTRY_PATH must be configured for poem resolution.")

        path = dataset_path.expanduser().resolve()
        if not path.exists():
            raise PoemResolutionError(f"Poem dataset not found: {path}")

        try:
            resolver = CanonicalRegistryResolver.from_path(self._settings.canonical_registry_path)
        except CanonicalRegistryError as exc:
            raise PoemResolutionError(str(exc)) from exc

        try:
            dataset = PoemPilotDataset.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise PoemResolutionError(f"Poem dataset is invalid: {path}") from exc

        resolved_output_path = (
            output_path.expanduser().resolve()
            if output_path is not None
            else path.with_name(f"{path.stem}.resolved.json")
        )
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

        resolved_poems: list[ResolvedPoemRecord] = []
        total_resolutions = 0
        matched_resolutions = 0
        proposed_new_resolutions = 0

        for poem in dataset.poems:
            author = resolver.resolve(entity_type=CanonicalEntityType.AUTHOR, label=poem.author)
            collection = resolver.resolve(entity_type=CanonicalEntityType.COLLECTION, label=poem.collection)
            source_language = resolver.resolve(
                entity_type=CanonicalEntityType.LANGUAGE,
                label=poem.source_language,
            )
            form = resolver.resolve(entity_type=CanonicalEntityType.LITERARY_WORK, label=poem.form)
            literary_unit = resolver.resolve(
                entity_type=CanonicalEntityType.LITERARY_UNIT,
                label=poem.literary_unit,
            )
            ontology = ResolvedOntologyTags(
                themes=[
                    resolver.resolve(entity_type=CanonicalEntityType.THEME, label=value)
                    for value in poem.ontology.themes
                ],
                human_experiences=[
                    resolver.resolve(entity_type=CanonicalEntityType.HUMAN_EXPERIENCE, label=value)
                    for value in poem.ontology.human_experiences
                ],
                symbols=[
                    resolver.resolve(entity_type=CanonicalEntityType.SYMBOL, label=value)
                    for value in poem.ontology.symbols
                ],
                concepts=[
                    resolver.resolve(entity_type=CanonicalEntityType.CONCEPT, label=value)
                    for value in poem.ontology.concepts
                ],
            )

            all_resolutions = [
                author,
                collection,
                source_language,
                form,
                literary_unit,
                *ontology.themes,
                *ontology.human_experiences,
                *ontology.symbols,
                *ontology.concepts,
            ]
            poem_total = len(all_resolutions)
            poem_matched = sum(1 for resolution in all_resolutions if resolution.matched_entry is not None)
            poem_proposed_new = sum(1 for resolution in all_resolutions if resolution.matched_entry is None)

            total_resolutions += poem_total
            matched_resolutions += poem_matched
            proposed_new_resolutions += poem_proposed_new

            resolved_poems.append(
                ResolvedPoemRecord(
                    poem_id=poem.poem_id,
                    title=poem.title,
                    author=author,
                    collection=collection,
                    source_language=source_language,
                    form=form,
                    literary_unit=literary_unit,
                    ontology=ontology,
                    total_resolutions=poem_total,
                    matched_resolutions=poem_matched,
                    proposed_new_resolutions=poem_proposed_new,
                )
            )

        resolved_dataset = PoemResolutionDataset(
            dataset_name=dataset.dataset_name,
            source_edition=dataset.source_edition,
            input_path=path,
            output_path=resolved_output_path,
            total_poems=len(dataset.poems),
            total_resolutions=total_resolutions,
            matched_resolutions=matched_resolutions,
            proposed_new_resolutions=proposed_new_resolutions,
            poems=resolved_poems,
        )
        resolved_output_path.write_text(
            json.dumps(resolved_dataset.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return PoemResolutionResult(
            dataset_name=resolved_dataset.dataset_name,
            input_path=resolved_dataset.input_path,
            output_path=resolved_dataset.output_path,
            total_poems=resolved_dataset.total_poems,
            total_resolutions=resolved_dataset.total_resolutions,
            matched_resolutions=resolved_dataset.matched_resolutions,
            proposed_new_resolutions=resolved_dataset.proposed_new_resolutions,
        )
