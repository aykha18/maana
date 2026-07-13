"""Materialize curator-reviewed poem datasets for downstream ingestion."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.config import Settings
from maana_ingest.ontology import CanonicalRegistryEntry, CanonicalRegistryError, CanonicalRegistryResolver
from maana_ingest.poems.models import (
    AppliedReviewFile,
    PoemResolutionDataset,
    ReviewedOntologyTags,
    ReviewedPoemDataset,
    ReviewedPoemRecord,
    ReviewedPoemResult,
    ReviewedResolution,
)


class ReviewedPoemMaterializationError(RuntimeError):
    """Raised when a reviewed poem dataset cannot be materialized."""


class ReviewedPoemDatasetService:
    """Combine resolved poem outputs with applied curator decisions."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def materialize_from_applied_review(
        self,
        applied_review_path: Path,
        *,
        output_path: Path | None = None,
    ) -> ReviewedPoemResult:
        applied_path = applied_review_path.expanduser().resolve()
        if not applied_path.exists():
            raise ReviewedPoemMaterializationError(f"Applied review file not found: {applied_path}")

        try:
            applied_review = AppliedReviewFile.model_validate_json(applied_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ReviewedPoemMaterializationError(f"Applied review file is invalid: {applied_path}") from exc

        review_path = applied_review.review_path.expanduser().resolve()
        if not review_path.exists():
            raise ReviewedPoemMaterializationError(f"Referenced review file not found: {review_path}")
        try:
            review_payload = json.loads(review_path.read_text(encoding="utf-8"))
            resolved_dataset_path = Path(review_payload["resolved_dataset_path"]).expanduser().resolve()
        except (KeyError, TypeError, ValueError) as exc:
            raise ReviewedPoemMaterializationError(
                f"Referenced review file is invalid: {review_path}"
            ) from exc

        if not resolved_dataset_path.exists():
            raise ReviewedPoemMaterializationError(
                f"Resolved poem dataset not found: {resolved_dataset_path}"
            )
        try:
            resolved_dataset = PoemResolutionDataset.model_validate_json(
                resolved_dataset_path.read_text(encoding="utf-8")
            )
        except ValueError as exc:
            raise ReviewedPoemMaterializationError(
                f"Resolved poem dataset is invalid: {resolved_dataset_path}"
            ) from exc

        registry_path = applied_review.registry_path.expanduser().resolve()
        try:
            registry = CanonicalRegistryResolver.from_path(registry_path).registry
        except CanonicalRegistryError as exc:
            raise ReviewedPoemMaterializationError(str(exc)) from exc

        decision_lookup = {
            (decision.entity_type.value, _normalize(decision.submitted_label)): decision
            for decision in applied_review.decisions
        }
        registry_lookup = {entry.canonical_id: entry for entry in registry.entries}

        reviewed_poems: list[ReviewedPoemRecord] = []
        fully_reviewed_poems = 0

        for poem in resolved_dataset.poems:
            author = self._materialize_resolution(poem.author, decision_lookup, registry_lookup)
            collection = self._materialize_resolution(poem.collection, decision_lookup, registry_lookup)
            source_language = self._materialize_resolution(
                poem.source_language,
                decision_lookup,
                registry_lookup,
            )
            form = self._materialize_resolution(poem.form, decision_lookup, registry_lookup)
            literary_unit = self._materialize_resolution(
                poem.literary_unit,
                decision_lookup,
                registry_lookup,
            )
            ontology = ReviewedOntologyTags(
                themes=[
                    self._materialize_resolution(resolution, decision_lookup, registry_lookup)
                    for resolution in poem.ontology.themes
                ],
                human_experiences=[
                    self._materialize_resolution(resolution, decision_lookup, registry_lookup)
                    for resolution in poem.ontology.human_experiences
                ],
                symbols=[
                    self._materialize_resolution(resolution, decision_lookup, registry_lookup)
                    for resolution in poem.ontology.symbols
                ],
                concepts=[
                    self._materialize_resolution(resolution, decision_lookup, registry_lookup)
                    for resolution in poem.ontology.concepts
                ],
            )

            all_reviewed = [
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
            fully_reviewed = all(
                item.review_status in {"matched", "approved_existing", "appended_new", "skipped_existing"}
                for item in all_reviewed
            )
            if fully_reviewed:
                fully_reviewed_poems += 1

            reviewed_poems.append(
                ReviewedPoemRecord(
                    poem_id=poem.poem_id,
                    title=poem.title,
                    author=author,
                    collection=collection,
                    source_language=source_language,
                    form=form,
                    literary_unit=literary_unit,
                    ontology=ontology,
                    fully_reviewed=fully_reviewed,
                )
            )

        reviewed_output_path = (
            output_path.expanduser().resolve()
            if output_path is not None
            else applied_path.with_name(f"{applied_path.stem}.reviewed.json")
        )
        reviewed_output_path.parent.mkdir(parents=True, exist_ok=True)
        reviewed_dataset = ReviewedPoemDataset(
            dataset_name=resolved_dataset.dataset_name,
            source_edition=resolved_dataset.source_edition,
            resolved_dataset_path=resolved_dataset_path,
            applied_review_path=applied_path,
            output_path=reviewed_output_path,
            total_poems=len(reviewed_poems),
            fully_reviewed_poems=fully_reviewed_poems,
            poems=reviewed_poems,
        )
        reviewed_output_path.write_text(
            json.dumps(reviewed_dataset.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return ReviewedPoemResult(
            dataset_name=reviewed_dataset.dataset_name,
            output_path=reviewed_dataset.output_path,
            total_poems=reviewed_dataset.total_poems,
            fully_reviewed_poems=reviewed_dataset.fully_reviewed_poems,
        )

    @staticmethod
    def _materialize_resolution(
        resolution: object,
        decision_lookup: dict[tuple[str, str], object],
        registry_lookup: dict[str, CanonicalRegistryEntry],
    ) -> ReviewedResolution:
        from maana_ingest.ontology.models import CanonicalResolution
        from maana_ingest.poems.models import AppliedReviewDecision

        if not isinstance(resolution, CanonicalResolution):
            raise ReviewedPoemMaterializationError("Resolved dataset contains an unexpected resolution object.")

        normalized_label = resolution.normalized_label
        if resolution.matched_entry is not None:
            return ReviewedResolution(
                entity_type=resolution.entity_type,
                submitted_label=resolution.submitted_label,
                normalized_label=normalized_label,
                review_status="matched",
                canonical_id=resolution.matched_entry.canonical_id,
                canonical_label=resolution.matched_entry.label,
            )

        key = (resolution.entity_type.value, normalized_label)
        decision = decision_lookup.get(key)
        if decision is None:
            return ReviewedResolution(
                entity_type=resolution.entity_type,
                submitted_label=resolution.submitted_label,
                normalized_label=normalized_label,
                review_status="unreviewed",
            )
        if not isinstance(decision, AppliedReviewDecision):
            raise ReviewedPoemMaterializationError("Applied review contains an unexpected decision object.")

        entry = registry_lookup.get(decision.resulting_canonical_id or "")
        return ReviewedResolution(
            entity_type=resolution.entity_type,
            submitted_label=resolution.submitted_label,
            normalized_label=normalized_label,
            review_status=decision.status,
            canonical_id=decision.resulting_canonical_id,
            canonical_label=entry.label if entry is not None else None,
        )


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())
