from __future__ import annotations

import json
from pathlib import Path
from shutil import copyfile
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.cli import app
from maana_ingest.poems import (
    CuratorDecision,
    PoemCuratorReviewService,
    PoemDatasetResolutionService,
    PoemReviewFile,
    ReviewAppendResult,
)


def test_generate_review_file_collects_unresolved_candidates(tmp_path: Path) -> None:
    registry_path = _copy_registry(tmp_path)
    dataset_path = _write_poem_dataset(tmp_path)
    resolution_service = PoemDatasetResolutionService(
        settings=SimpleNamespace(canonical_registry_path=registry_path)
    )
    resolved = resolution_service.resolve_dataset(dataset_path)

    review_service = PoemCuratorReviewService(settings=SimpleNamespace(canonical_registry_path=registry_path))
    review = review_service.generate_review_file(resolved.output_path)

    assert review.total_candidates == 1
    assert review.pending_candidates == 1
    assert review.candidates[0].entity_type.value == "symbol"
    assert review.candidates[0].submitted_label == "nightingale"
    assert review.candidates[0].suggested_canonical_id == "symbol.nightingale"


def test_append_approved_terms_adds_new_registry_entry(tmp_path: Path) -> None:
    registry_path = _copy_registry(tmp_path)
    dataset_path = _write_poem_dataset(tmp_path)
    resolution_service = PoemDatasetResolutionService(
        settings=SimpleNamespace(canonical_registry_path=registry_path)
    )
    resolved = resolution_service.resolve_dataset(dataset_path)

    review_service = PoemCuratorReviewService(settings=SimpleNamespace(canonical_registry_path=registry_path))
    review = review_service.generate_review_file(resolved.output_path)

    review_payload = json.loads(review.review_path.read_text(encoding="utf-8"))
    review_payload["candidates"][0]["decision"] = CuratorDecision.CREATE_NEW.value
    review_payload["candidates"][0]["description"] = "A recurring bird symbol in Persianate and Urdu poetry."
    review_payload["candidates"][0]["aliases"] = ["bulbul"]
    review_payload["candidates"][0]["notes"] = "Approved during first Ghalib pilot."
    review.review_path.write_text(json.dumps(review_payload, indent=2), encoding="utf-8")

    result = review_service.append_approved_terms(review.review_path)

    assert result.appended_entries == 1
    assert result.skipped_existing == 0
    assert result.approved_existing == 0
    assert result.applied_path.exists()
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    matching_entries = [entry for entry in registry_payload["entries"] if entry["canonical_id"] == "symbol.nightingale"]
    assert len(matching_entries) == 1
    assert matching_entries[0]["aliases"] == ["bulbul"]
    applied_payload = json.loads(result.applied_path.read_text(encoding="utf-8"))
    assert applied_payload["decisions"][0]["status"] == "appended_new"


def test_append_approved_terms_persists_approve_existing_without_registry_mutation(tmp_path: Path) -> None:
    registry_path = _copy_registry(tmp_path)
    dataset_path = _write_poem_dataset(tmp_path)
    resolution_service = PoemDatasetResolutionService(
        settings=SimpleNamespace(canonical_registry_path=registry_path)
    )
    resolved = resolution_service.resolve_dataset(dataset_path)

    review_service = PoemCuratorReviewService(settings=SimpleNamespace(canonical_registry_path=registry_path))
    review = review_service.generate_review_file(resolved.output_path)

    review_payload = json.loads(review.review_path.read_text(encoding="utf-8"))
    review_payload["candidates"][0]["decision"] = CuratorDecision.APPROVE_EXISTING.value
    review_payload["candidates"][0]["existing_canonical_id"] = "symbol.mirror"
    review_payload["candidates"][0]["notes"] = "Mapped by curator to the nearest canonical symbol for pilot consistency."
    review.review_path.write_text(json.dumps(review_payload, indent=2), encoding="utf-8")

    result = review_service.append_approved_terms(review.review_path)

    assert result.appended_entries == 0
    assert result.skipped_existing == 0
    assert result.approved_existing == 1
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    matching_entries = [entry for entry in registry_payload["entries"] if entry["canonical_id"] == "symbol.nightingale"]
    assert matching_entries == []
    applied_payload = json.loads(result.applied_path.read_text(encoding="utf-8"))
    assert applied_payload["decisions"][0]["status"] == "approved_existing"
    assert applied_payload["decisions"][0]["resulting_canonical_id"] == "symbol.mirror"


def test_prepare_poem_review_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = PoemReviewFile(
        dataset_name="ghalib-pilot",
        source_edition="Nuskha-e-Hamidiya",
        resolved_dataset_path=tmp_path / "pilot.resolved.json",
        review_path=tmp_path / "pilot.review.json",
        total_candidates=3,
        pending_candidates=3,
        candidates=[],
    )

    def fake_generate_review_file(
        self: object,
        resolved_dataset_path: Path,
        *,
        output_path: Path | None = None,
    ) -> PoemReviewFile:
        return expected

    monkeypatch.setattr(PoemCuratorReviewService, "generate_review_file", fake_generate_review_file)

    result = runner.invoke(app, ["prepare-poem-review", str(tmp_path / "pilot.resolved.json")])

    assert result.exit_code == 0
    assert "Dataset: ghalib-pilot" in result.stdout
    assert "Total candidates: 3" in result.stdout


def test_append_approved_terms_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = ReviewAppendResult(
        review_path=tmp_path / "pilot.review.json",
        registry_path=tmp_path / "canonical_registry.json",
        applied_path=tmp_path / "pilot.review.applied.json",
        appended_entries=2,
        skipped_existing=1,
        approved_existing=3,
        pending_or_rejected=4,
    )

    def fake_append_approved_terms(self: object, review_path: Path) -> ReviewAppendResult:
        return expected

    monkeypatch.setattr(PoemCuratorReviewService, "append_approved_terms", fake_append_approved_terms)

    result = runner.invoke(app, ["append-approved-terms", str(tmp_path / "pilot.review.json")])

    assert result.exit_code == 0
    assert "Applied path:" in result.stdout
    assert "Appended entries: 2" in result.stdout
    assert "Skipped existing: 1" in result.stdout
    assert "Approved existing: 3" in result.stdout


def _write_poem_dataset(base_dir: Path) -> Path:
    dataset_path = base_dir / "ghalib-pilot.json"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_name": "ghalib-pilot",
                "source_edition": "Nuskha-e-Hamidiya",
                "poems": [
                    {
                        "poem_id": "ghalib-001",
                        "title": "Hazaron Khwahishen Aisi",
                        "author": "Mirza Ghalib",
                        "collection": "Diwan-e-Ghalib",
                        "source_language": "Urdu",
                        "form": "Ghazal",
                        "literary_unit": "Couplet",
                        "source_edition": "Nuskha-e-Hamidiya",
                        "verses": [
                            {
                                "unit_number": 1,
                                "text": "hazaron khwahishen aisi ke har khwahish pe dam nikle"
                            }
                        ],
                        "translations": [],
                        "commentary_references": [],
                        "ontology": {
                            "themes": ["memory"],
                            "human_experiences": ["longing"],
                            "symbols": ["nightingale"],
                            "concepts": ["absence"]
                        }
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return dataset_path


def _copy_registry(base_dir: Path) -> Path:
    target = base_dir / "canonical_registry.json"
    copyfile(_repo_registry_path(), target)
    return target


def _repo_registry_path() -> Path:
    return Path(__file__).resolve().parents[1] / "registry" / "canonical_registry.json"
