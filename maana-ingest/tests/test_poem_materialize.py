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
    ReviewedPoemDatasetService,
    ReviewedPoemResult,
)


def test_materialize_reviewed_poem_dataset_builds_final_output(tmp_path: Path) -> None:
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
    review.review_path.write_text(json.dumps(review_payload, indent=2), encoding="utf-8")

    append_result = review_service.append_approved_terms(review.review_path)

    materialize_service = ReviewedPoemDatasetService(
        settings=SimpleNamespace(canonical_registry_path=registry_path)
    )
    result = materialize_service.materialize_from_applied_review(append_result.applied_path)

    assert result.total_poems == 1
    assert result.fully_reviewed_poems == 1
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))
    symbol = payload["poems"][0]["ontology"]["symbols"][0]
    assert symbol["review_status"] == "appended_new"
    assert symbol["canonical_id"] == "symbol.nightingale"
    assert symbol["canonical_label"] == "nightingale"


def test_materialize_reviewed_poem_dataset_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = ReviewedPoemResult(
        dataset_name="ghalib-pilot",
        output_path=tmp_path / "pilot.reviewed.json",
        total_poems=10,
        fully_reviewed_poems=8,
    )

    def fake_materialize_from_applied_review(
        self: object,
        applied_review_path: Path,
        *,
        output_path: Path | None = None,
    ) -> ReviewedPoemResult:
        return expected

    monkeypatch.setattr(
        ReviewedPoemDatasetService,
        "materialize_from_applied_review",
        fake_materialize_from_applied_review,
    )

    result = runner.invoke(app, ["materialize-reviewed-poem-dataset", str(tmp_path / "pilot.applied.json")])

    assert result.exit_code == 0
    assert "Dataset: ghalib-pilot" in result.stdout
    assert "Fully reviewed poems: 8" in result.stdout


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
