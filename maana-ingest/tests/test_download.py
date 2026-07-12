from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from maana_ingest.cli import app
from maana_ingest.cli.app import YtDlpDownloadService as CliDownloadService
from maana_ingest.download import LectureWorkspace, YtDlpDownloadService
from maana_ingest.models import DownloadResult, SourceMetadata, SourceRequest


class FakeYoutubeDL:
    def __init__(self, options: dict[str, Any], info: dict[str, Any]) -> None:
        self.options = options
        self.info = info

    def __enter__(self) -> "FakeYoutubeDL":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def extract_info(self, url: str, download: bool = False) -> dict[str, Any]:
        if download:
            outtmpl = self.options["outtmpl"]
            media_path = Path(outtmpl.replace("%(ext)s", "m4a"))
            media_path.parent.mkdir(parents=True, exist_ok=True)
            media_path.write_text("audio-bytes", encoding="utf-8")
            media_path.parent.joinpath("source.en.vtt").write_text("subtitle", encoding="utf-8")
            media_path.parent.joinpath("source.webp").write_text("thumbnail", encoding="utf-8")
        return dict(self.info)

    def prepare_filename(self, info_dict: dict[str, Any]) -> str:
        outtmpl = self.options.get("outtmpl")
        if outtmpl is None:
            raise KeyError("outtmpl")
        return outtmpl.replace("%(ext)s", "m4a")


class FakeYdlFactory:
    def __init__(self, info: dict[str, Any]) -> None:
        self.info = info
        self.calls: list[dict[str, Any]] = []

    def __call__(self, options: dict[str, Any]) -> FakeYoutubeDL:
        self.calls.append(options)
        return FakeYoutubeDL(options, self.info)


def test_workspace_layout_is_deterministic(tmp_path: Path) -> None:
    metadata = SourceMetadata(
        title="Ghalib aur Maana",
        speaker="Ahmed Javed",
        duration=3600,
        upload_date="20260712",
        youtube_id="abc123xyz",
        description="Lecture description",
        thumbnail="https://example.com/thumb.webp",
        channel="Danish Sara",
        original_url="https://youtu.be/abc123xyz",
    )

    workspace = LectureWorkspace.build(tmp_path, metadata)

    assert workspace.lecture_root == tmp_path / "lectures" / "ahmed-javed" / "abc123xyz-ghalib-aur-maana"
    assert workspace.source_dir == workspace.lecture_root / "source"
    assert workspace.metadata_path == workspace.lecture_root / "metadata" / "metadata.json"


def test_download_service_persists_workspace_files(tmp_path: Path) -> None:
    info = {
        "id": "abc123xyz",
        "title": "Ghalib aur Maana",
        "uploader": "Ahmed Javed",
        "channel": "Danish Sara",
        "duration": 3600,
        "upload_date": "20260712",
        "description": "Lecture description",
        "thumbnail": "https://example.com/thumb.webp",
    }
    factory = FakeYdlFactory(info)
    request = SourceRequest(url="https://youtu.be/abc123xyz", output_dir=tmp_path)
    settings = type("SettingsLike", (), {"download_retries": 2})()

    service = YtDlpDownloadService(settings=settings, ydl_factory=factory)
    result = service.download(request)

    assert result.skipped is False
    assert result.raw_media_path is not None
    assert result.raw_media_path.name == "source.m4a"
    assert result.metadata_path.exists()
    assert result.raw_info_path.exists()
    assert result.source_request_path.exists()
    assert {path.name for path in result.downloaded_files} == {
        "source.en.vtt",
        "source.m4a",
        "source.webp",
    }

    second_result = service.download(request)
    assert second_result.skipped is True
    assert second_result.raw_media_path == result.raw_media_path


def test_download_cli_reports_workspace(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    expected = DownloadResult(
        request=SourceRequest(url="https://youtu.be/demo123", output_dir=tmp_path),
        lecture_root=tmp_path / "lectures" / "speaker" / "demo123-title",
        source_dir=tmp_path / "lectures" / "speaker" / "demo123-title" / "source",
        metadata_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "metadata" / "metadata.json",
        raw_info_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "metadata" / "raw_info.json",
        source_request_path=tmp_path
        / "lectures"
        / "speaker"
        / "demo123-title"
        / "metadata"
        / "source_request.json",
        raw_media_path=tmp_path / "lectures" / "speaker" / "demo123-title" / "source" / "source.m4a",
        skipped=False,
        downloaded_files=[],
    )

    def fake_download(self: object, request: SourceRequest) -> DownloadResult:
        return expected

    monkeypatch.setattr(CliDownloadService, "download", fake_download)

    result = runner.invoke(
        app,
        ["download", "https://youtu.be/demo123", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "Lecture workspace:" in result.stdout
    assert str(expected.raw_media_path) in result.stdout
