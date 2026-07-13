"""Canonical registry loading and exact-match resolution scaffolding."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from maana_ingest.ontology.models import (
    CanonicalEntityCandidate,
    CanonicalEntityType,
    CanonicalMappingStatus,
    CanonicalRegistry,
    CanonicalRegistryEntry,
    CanonicalResolution,
)


class CanonicalRegistryError(RuntimeError):
    """Raised when the canonical registry cannot be loaded or resolved."""


class CanonicalRegistryResolver:
    """Resolve extracted ontology labels against a curated canonical registry."""

    def __init__(self, registry: CanonicalRegistry) -> None:
        self._registry = registry
        self._index = self._build_index(registry.entries)

    @classmethod
    def from_path(cls, path: Path) -> "CanonicalRegistryResolver":
        resolved_path = path.expanduser().resolve()
        if not resolved_path.exists():
            raise CanonicalRegistryError(f"Canonical registry not found: {resolved_path}")
        try:
            registry = CanonicalRegistry.model_validate_json(resolved_path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            raise CanonicalRegistryError(
                f"Canonical registry is invalid: {resolved_path}"
            ) from exc
        return cls(registry)

    @property
    def registry(self) -> CanonicalRegistry:
        """Return the loaded registry."""

        return self._registry

    def resolve(
        self,
        *,
        entity_type: CanonicalEntityType,
        label: str,
    ) -> CanonicalResolution:
        normalized_label = normalize_registry_label(label)
        if not normalized_label:
            raise CanonicalRegistryError("Cannot resolve an empty canonical label.")

        matched_entry = self._index.get((entity_type, normalized_label))
        if matched_entry is not None:
            return CanonicalResolution(
                entity_type=entity_type,
                submitted_label=label,
                normalized_label=normalized_label,
                mapping_status=CanonicalMappingStatus.MATCHED,
                matched_entry=matched_entry,
                matched_on="label_or_alias",
                rationale="Exact normalized match found in canonical registry.",
            )

        return CanonicalResolution(
            entity_type=entity_type,
            submitted_label=label,
            normalized_label=normalized_label,
            mapping_status=CanonicalMappingStatus.PROPOSED_NEW,
            rationale="No exact canonical match found; curator review is required.",
        )

    def resolve_candidate(self, candidate: CanonicalEntityCandidate) -> CanonicalEntityCandidate:
        """Return a candidate with canonical resolution fields populated."""

        resolution = self.resolve(entity_type=candidate.entity_type, label=candidate.label)
        candidate.normalized_label = resolution.normalized_label
        candidate.mapping_status = resolution.mapping_status
        candidate.rationale = resolution.rationale
        if resolution.matched_entry is not None:
            candidate.canonical_id = resolution.matched_entry.canonical_id
            candidate.aliases = sorted(
                set(candidate.aliases).union(resolution.matched_entry.aliases)
            )
        return candidate

    @staticmethod
    def _build_index(
        entries: list[CanonicalRegistryEntry],
    ) -> dict[tuple[CanonicalEntityType, str], CanonicalRegistryEntry]:
        index: dict[tuple[CanonicalEntityType, str], CanonicalRegistryEntry] = {}
        for entry in entries:
            keys = {normalize_registry_label(entry.label)}
            keys.update(normalize_registry_label(alias) for alias in entry.aliases)
            keys.discard("")
            for key in keys:
                index[(entry.entity_type, key)] = entry
        return index


def normalize_registry_label(value: str) -> str:
    """Normalize labels for deterministic exact matching."""

    return " ".join(value.strip().lower().split())
