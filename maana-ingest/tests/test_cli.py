from typer.testing import CliRunner

from maana_ingest.cli import app


def test_root_help_shows_usage() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Maana ingestion pipeline CLI." in result.stdout
