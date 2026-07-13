from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from maana_ingest.cli import app
from maana_ingest.poems import PoemDatasetResolutionService, PoemResolutionResult


def test_poem_dataset_resolution_writes_output(tmp_path: Path) -> None:
    dataset_path = _write_poem_dataset(tmp_path)
    settings = SimpleNamespace(canonical_registry_path=_registry_path())

    service = PoemDatasetResolutionService(settings=settings)
    result = service.resolve_dataset(dataset_path)

    assert result.total_poems == 1
    assert result.total_resolutions == 9
    assert result.matched_resolutions == 8
    assert result.proposed_new_resolutions == 1
    assert result.output_path.exists()

    payload = json.loads(result.output_path.read_text(encoding="utf-8"))
    assert payload["poems"][0]["author"]["matched_entry"]["canonical_id"] == "author.ghalib"
    assert payload["poems"][0]["ontology"]["symbols"][0]["mapping_status"] == "proposed_new"


def test_resolve_poem_dataset_cli_reports_summary(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = PoemResolutionResult(
        dataset_name="diwan-e-ghalib-first-10",
        input_path=tmp_path / "pilot.json",
        output_path=tmp_path / "pilot.resolved.json",
        total_poems=10,
        total_resolutions=90,
        matched_resolutions=74,
        proposed_new_resolutions=16,
    )

    def fake_resolve_dataset(
        self: object,
        dataset_path: Path,
        *,
        output_path: Path | None = None,
    ) -> PoemResolutionResult:
        return expected

    monkeypatch.setattr(PoemDatasetResolutionService, "resolve_dataset", fake_resolve_dataset)

    result = runner.invoke(app, ["resolve-poem-dataset", str(tmp_path / "pilot.json")])

    assert result.exit_code == 0
    assert "Dataset: diwan-e-ghalib-first-10" in result.stdout
    assert "Total poems: 10" in result.stdout
    assert "Proposed new resolutions: 16" in result.stdout


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
                            },
                            {
                                "unit_number": 2,
                                "text": "bahut nikle mere arman lekin phir bhi kam nikle"
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


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "registry"
        / "canonical_registry.json"
    )
