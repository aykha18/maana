from __future__ import annotations

from pathlib import Path

from maana_ingest.ontology import (
    CanonicalEntityCandidate,
    CanonicalEntityType,
    CanonicalMappingStatus,
    CanonicalRegistryResolver,
)


def test_registry_seed_loads_and_matches_known_alias() -> None:
    registry_path = _registry_path()
    resolver = CanonicalRegistryResolver.from_path(registry_path)

    resolution = resolver.resolve(
        entity_type=CanonicalEntityType.COLLECTION,
        label="diwan ghalib",
    )

    assert resolution.mapping_status is CanonicalMappingStatus.MATCHED
    assert resolution.matched_entry is not None
    assert resolution.matched_entry.canonical_id == "collection.diwan-e-ghalib"


def test_registry_marks_unknown_entity_as_proposed_new() -> None:
    registry_path = _registry_path()
    resolver = CanonicalRegistryResolver.from_path(registry_path)

    resolution = resolver.resolve(
        entity_type=CanonicalEntityType.SYMBOL,
        label="nightingale",
    )

    assert resolution.mapping_status is CanonicalMappingStatus.PROPOSED_NEW
    assert resolution.matched_entry is None


def test_resolve_candidate_populates_candidate_fields() -> None:
    registry_path = _registry_path()
    resolver = CanonicalRegistryResolver.from_path(registry_path)
    candidate = CanonicalEntityCandidate(
        entity_type=CanonicalEntityType.AUTHOR,
        label="Mirza Ghalib",
    )

    resolved = resolver.resolve_candidate(candidate)

    assert resolved.mapping_status is CanonicalMappingStatus.MATCHED
    assert resolved.canonical_id == "author.ghalib"
    assert resolved.normalized_label == "mirza ghalib"


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "registry"
        / "canonical_registry.json"
    )
