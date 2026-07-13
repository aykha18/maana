"""Curator review-file generation and registry-append workflow for poem pilots."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.config import Settings
from maana_ingest.ontology import (
    CanonicalEntityType,
    CanonicalMappingStatus,
    CanonicalRegistry,
    CanonicalRegistryEntry,
    CanonicalRegistryError,
    CanonicalRegistryResolver,
    normalize_registry_label,
)
from maana_ingest.poems.models import (
    AppliedReviewDecision,
    AppliedReviewFile,
    CuratorDecision,
    PoemResolutionDataset,
    PoemReviewFile,
    ReviewAppendResult,
    ReviewCandidate,
    ReviewOccurrence,
)


class PoemCuratorReviewError(RuntimeError):
    """Raised when review files cannot be generated or applied."""


class PoemCuratorReviewService:
    """Prepare curator review queues and append approved ontology terms to the registry."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_review_file(
        self,
        resolved_dataset_path: Path,
        *,
        output_path: Path | None = None,
    ) -> PoemReviewFile:
        dataset_path = resolved_dataset_path.expanduser().resolve()
        if not dataset_path.exists():
            raise PoemCuratorReviewError(f"Resolved poem dataset not found: {dataset_path}")

        try:
            dataset = PoemResolutionDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise PoemCuratorReviewError(f"Resolved poem dataset is invalid: {dataset_path}") from exc

        review_output_path = (
            output_path.expanduser().resolve()
            if output_path is not None
            else dataset_path.with_name(f"{dataset_path.stem}.review.json")
        )
        review_output_path.parent.mkdir(parents=True, exist_ok=True)

        candidate_lookup: dict[tuple[CanonicalEntityType, str], ReviewCandidate] = {}

        for poem in dataset.poems:
            self._collect_candidate(
                candidate_lookup,
                resolution=poem.author,
                poem_id=poem.poem_id,
                title=poem.title,
                field_path="author",
            )
            self._collect_candidate(
                candidate_lookup,
                resolution=poem.collection,
                poem_id=poem.poem_id,
                title=poem.title,
                field_path="collection",
            )
            self._collect_candidate(
                candidate_lookup,
                resolution=poem.source_language,
                poem_id=poem.poem_id,
                title=poem.title,
                field_path="source_language",
            )
            self._collect_candidate(
                candidate_lookup,
                resolution=poem.form,
                poem_id=poem.poem_id,
                title=poem.title,
                field_path="form",
            )
            self._collect_candidate(
                candidate_lookup,
                resolution=poem.literary_unit,
                poem_id=poem.poem_id,
                title=poem.title,
                field_path="literary_unit",
            )
            for index, resolution in enumerate(poem.ontology.themes, start=1):
                self._collect_candidate(
                    candidate_lookup,
                    resolution=resolution,
                    poem_id=poem.poem_id,
                    title=poem.title,
                    field_path=f"ontology.themes[{index}]",
                )
            for index, resolution in enumerate(poem.ontology.human_experiences, start=1):
                self._collect_candidate(
                    candidate_lookup,
                    resolution=resolution,
                    poem_id=poem.poem_id,
                    title=poem.title,
                    field_path=f"ontology.human_experiences[{index}]",
                )
            for index, resolution in enumerate(poem.ontology.symbols, start=1):
                self._collect_candidate(
                    candidate_lookup,
                    resolution=resolution,
                    poem_id=poem.poem_id,
                    title=poem.title,
                    field_path=f"ontology.symbols[{index}]",
                )
            for index, resolution in enumerate(poem.ontology.concepts, start=1):
                self._collect_candidate(
                    candidate_lookup,
                    resolution=resolution,
                    poem_id=poem.poem_id,
                    title=poem.title,
                    field_path=f"ontology.concepts[{index}]",
                )

        candidates = sorted(
            candidate_lookup.values(),
            key=lambda candidate: (candidate.entity_type.value, candidate.normalized_label),
        )
        review_file = PoemReviewFile(
            dataset_name=dataset.dataset_name,
            source_edition=dataset.source_edition,
            resolved_dataset_path=dataset_path,
            review_path=review_output_path,
            total_candidates=len(candidates),
            pending_candidates=len(candidates),
            candidates=candidates,
        )
        review_output_path.write_text(
            json.dumps(review_file.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return review_file

    def append_approved_terms(self, review_path: Path) -> ReviewAppendResult:
        if self._settings.canonical_registry_path is None:
            raise PoemCuratorReviewError("CANONICAL_REGISTRY_PATH must be configured to append approved terms.")

        resolved_review_path = review_path.expanduser().resolve()
        if not resolved_review_path.exists():
            raise PoemCuratorReviewError(f"Review file not found: {resolved_review_path}")

        try:
            review_file = PoemReviewFile.model_validate_json(resolved_review_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise PoemCuratorReviewError(f"Review file is invalid: {resolved_review_path}") from exc

        registry_path = self._settings.canonical_registry_path.expanduser().resolve()
        try:
            resolver = CanonicalRegistryResolver.from_path(registry_path)
        except CanonicalRegistryError as exc:
            raise PoemCuratorReviewError(str(exc)) from exc

        registry = resolver.registry.model_copy(deep=True)
        working_resolver = CanonicalRegistryResolver(registry)
        applied_path = resolved_review_path.with_name(f"{resolved_review_path.stem}.applied.json")
        appended_entries = 0
        skipped_existing = 0
        approved_existing = 0
        pending_or_rejected = 0
        applied_decisions: list[AppliedReviewDecision] = []

        for candidate in review_file.candidates:
            if candidate.decision is CuratorDecision.APPROVE_EXISTING:
                existing_canonical_id = (candidate.existing_canonical_id or "").strip()
                if not existing_canonical_id:
                    raise PoemCuratorReviewError(
                        "approve_existing requires existing_canonical_id "
                        f"for candidate {candidate.entity_type.value}:{candidate.submitted_label}"
                    )
                existing_entry = _find_registry_entry_by_id(registry, existing_canonical_id)
                if existing_entry is None:
                    raise PoemCuratorReviewError(
                        f"Existing canonical ID not found in registry: {existing_canonical_id}"
                    )
                if existing_entry.entity_type is not candidate.entity_type:
                    raise PoemCuratorReviewError(
                        "Existing canonical ID has the wrong entity type "
                        f"for candidate {candidate.entity_type.value}:{candidate.submitted_label}"
                    )
                approved_existing += 1
                applied_decisions.append(
                    AppliedReviewDecision(
                        entity_type=candidate.entity_type,
                        submitted_label=candidate.submitted_label,
                        decision=candidate.decision,
                        resulting_canonical_id=existing_entry.canonical_id,
                        status="approved_existing",
                        notes=candidate.notes,
                    )
                )
                continue

            if candidate.decision is not CuratorDecision.CREATE_NEW:
                pending_or_rejected += 1
                applied_decisions.append(
                    AppliedReviewDecision(
                        entity_type=candidate.entity_type,
                        submitted_label=candidate.submitted_label,
                        decision=candidate.decision,
                        status="pending_or_rejected",
                        notes=candidate.notes,
                    )
                )
                continue

            approved_label = (candidate.approved_label or candidate.submitted_label).strip()
            if not approved_label:
                raise PoemCuratorReviewError(
                    f"Approved label is empty for candidate {candidate.entity_type.value}:{candidate.submitted_label}"
                )

            resolution = working_resolver.resolve(
                entity_type=candidate.entity_type,
                label=approved_label,
            )
            if resolution.mapping_status is CanonicalMappingStatus.MATCHED:
                skipped_existing += 1
                applied_decisions.append(
                    AppliedReviewDecision(
                        entity_type=candidate.entity_type,
                        submitted_label=candidate.submitted_label,
                        decision=candidate.decision,
                        resulting_canonical_id=resolution.matched_entry.canonical_id if resolution.matched_entry else None,
                        status="skipped_existing",
                        notes=candidate.notes,
                    )
                )
                continue

            canonical_id = candidate.suggested_canonical_id.strip() or build_canonical_id(
                candidate.entity_type,
                approved_label,
            )
            if any(entry.canonical_id == canonical_id for entry in registry.entries):
                raise PoemCuratorReviewError(f"Canonical ID already exists in registry: {canonical_id}")

            entry = CanonicalRegistryEntry(
                canonical_id=canonical_id,
                entity_type=candidate.entity_type,
                label=approved_label,
                normalized_label=normalize_registry_label(approved_label),
                description=candidate.description,
                aliases=sorted({alias.strip() for alias in candidate.aliases if alias.strip()}),
                source_notes=_build_source_notes(review_file.dataset_name, candidate.notes),
            )
            registry.entries.append(entry)
            working_resolver = CanonicalRegistryResolver(registry)
            appended_entries += 1
            applied_decisions.append(
                AppliedReviewDecision(
                    entity_type=candidate.entity_type,
                    submitted_label=candidate.submitted_label,
                    decision=candidate.decision,
                    resulting_canonical_id=entry.canonical_id,
                    status="appended_new",
                    notes=candidate.notes,
                )
            )

        registry.entries.sort(key=lambda entry: (entry.entity_type.value, entry.normalized_label or entry.label.lower()))
        registry_path.write_text(
            json.dumps(registry.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        applied_file = AppliedReviewFile(
            dataset_name=review_file.dataset_name,
            source_edition=review_file.source_edition,
            review_path=resolved_review_path,
            registry_path=registry_path,
            applied_path=applied_path,
            appended_entries=appended_entries,
            skipped_existing=skipped_existing,
            approved_existing=approved_existing,
            pending_or_rejected=pending_or_rejected,
            decisions=applied_decisions,
        )
        applied_path.write_text(
            json.dumps(applied_file.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return ReviewAppendResult(
            review_path=resolved_review_path,
            registry_path=registry_path,
            applied_path=applied_path,
            appended_entries=appended_entries,
            skipped_existing=skipped_existing,
            approved_existing=approved_existing,
            pending_or_rejected=pending_or_rejected,
        )

    @staticmethod
    def _collect_candidate(
        candidate_lookup: dict[tuple[CanonicalEntityType, str], ReviewCandidate],
        *,
        resolution: object,
        poem_id: str,
        title: str,
        field_path: str,
    ) -> None:
        from maana_ingest.ontology.models import CanonicalResolution

        if not isinstance(resolution, CanonicalResolution):
            raise PoemCuratorReviewError("Resolved poem dataset contains an unexpected resolution object.")
        if resolution.mapping_status is not CanonicalMappingStatus.PROPOSED_NEW:
            return

        key = (resolution.entity_type, resolution.normalized_label)
        candidate = candidate_lookup.get(key)
        if candidate is None:
            candidate = ReviewCandidate(
                entity_type=resolution.entity_type,
                submitted_label=resolution.submitted_label,
                normalized_label=resolution.normalized_label,
                suggested_canonical_id=build_canonical_id(
                    resolution.entity_type,
                    resolution.submitted_label,
                ),
            )
            candidate_lookup[key] = candidate

        candidate.occurrences.append(
            ReviewOccurrence(
                poem_id=poem_id,
                title=title,
                field_path=field_path,
                submitted_label=resolution.submitted_label,
            )
        )


def build_canonical_id(entity_type: CanonicalEntityType, label: str) -> str:
    """Create a deterministic canonical ID for new approved entities."""

    prefix_map = {
        CanonicalEntityType.HUMAN_EXPERIENCE: "experience",
        CanonicalEntityType.LITERARY_WORK: "literary-work",
        CanonicalEntityType.LITERARY_UNIT: "literary-unit",
    }
    prefix = prefix_map.get(entity_type, entity_type.value.replace("_", "-"))
    slug = _slugify_registry_label(label)
    return f"{prefix}.{slug}"


def _slugify_registry_label(value: str) -> str:
    normalized = normalize_registry_label(value)
    return normalized.replace(" ", "-")


def _build_source_notes(dataset_name: str, notes: str | None) -> list[str]:
    source_notes = [f"Approved from poem review dataset: {dataset_name}"]
    if notes:
        source_notes.append(notes.strip())
    return source_notes


def _find_registry_entry_by_id(
    registry: CanonicalRegistry,
    canonical_id: str,
) -> CanonicalRegistryEntry | None:
    for entry in registry.entries:
        if entry.canonical_id == canonical_id:
            return entry
    return None
