"""yt-dlp powered source download service."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from loguru import logger
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from maana_ingest.config import Settings
from maana_ingest.download.workspace import LectureWorkspace
from maana_ingest.models import DownloadResult, SourceMetadata, SourceRequest, SourceType


class DownloadStageError(RuntimeError):
    """Raised when the download stage fails."""


class YoutubeDllike(Protocol):
    """Protocol for testable yt-dlp interactions."""

    def __enter__(self) -> "YoutubeDllike": ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...

    def extract_info(self, url: str, download: bool = False) -> dict[str, Any]: ...

    def prepare_filename(self, info_dict: dict[str, Any]) -> str: ...


YdlFactory = Callable[[dict[str, Any]], YoutubeDllike]


class YtDlpDownloadService:
    """Download source media and metadata into a lecture workspace."""

    def __init__(self, settings: Settings, ydl_factory: YdlFactory | None = None) -> None:
        self._settings = settings
        self._ydl_factory = ydl_factory or self._create_ydl

    def download(self, request: SourceRequest) -> DownloadResult:
        if request.source_type is not SourceType.YOUTUBE:
            raise DownloadStageError(f"Unsupported source type: {request.source_type}")

        info = self._extract_info(request)
        metadata = SourceMetadata.from_yt_dlp_info(info, original_url=request.url)
        workspace = LectureWorkspace.build(request.output_dir, metadata)
        workspace.ensure_exists()
        self._write_json(workspace.source_request_path, request.model_dump(mode="json"))
        self._write_json(workspace.raw_info_path, info)
        self._write_json(workspace.metadata_path, metadata.model_dump(mode="json"))

        existing_media = workspace.find_raw_media_path()
        if existing_media is not None:
            logger.info("Download artifacts already exist at {}", workspace.lecture_root)
            return self._build_result(request, workspace, existing_media, skipped=True)

        downloaded_info = self._download_source(request, workspace)
        metadata = SourceMetadata.from_yt_dlp_info(downloaded_info, original_url=request.url)
        self._write_json(workspace.raw_info_path, downloaded_info)
        self._write_json(workspace.metadata_path, metadata.model_dump(mode="json"))

        raw_media_path = self._resolve_raw_media_path(workspace, downloaded_info)
        if raw_media_path is None:
            raise DownloadStageError("yt-dlp completed but no source media file was found")

        logger.info("Downloaded source media to {}", raw_media_path)
        return self._build_result(request, workspace, raw_media_path, skipped=False)

    def _extract_info(self, request: SourceRequest) -> dict[str, Any]:
        options = self._base_options()
        with self._ydl_factory(options) as ydl:
            try:
                info = ydl.extract_info(request.url, download=False)
            except DownloadError as exc:
                raise DownloadStageError(f"Failed to inspect source URL: {request.url}") from exc
        return info

    def _download_source(
        self,
        request: SourceRequest,
        workspace: LectureWorkspace,
    ) -> dict[str, Any]:
        options = self._base_options()
        options.update(
            {
                "format": "bestaudio/best",
                "noplaylist": True,
                "nooverwrites": True,
                "continuedl": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "writethumbnail": True,
                "skip_download": False,
                "outtmpl": str(workspace.source_dir / "source.%(ext)s"),
            }
        )

        last_error: DownloadError | None = None
        for attempt in range(1, self._settings.download_retries + 1):
            logger.info("Download attempt {} of {}", attempt, self._settings.download_retries)
            try:
                with self._ydl_factory(options) as ydl:
                    return ydl.extract_info(request.url, download=True)
            except DownloadError as exc:
                last_error = exc
                logger.warning("Download attempt {} failed: {}", attempt, exc)

        raise DownloadStageError(f"Failed to download source after retries: {request.url}") from last_error

    def _resolve_raw_media_path(
        self,
        workspace: LectureWorkspace,
        downloaded_info: dict[str, Any],
    ) -> Path | None:
        prepared_path = None
        with self._ydl_factory(self._base_options()) as ydl:
            try:
                prepared_path = Path(ydl.prepare_filename(downloaded_info))
            except Exception:
                prepared_path = None

        if prepared_path is not None and prepared_path.exists():
            return prepared_path.resolve()
        return workspace.find_raw_media_path()

    def _build_result(
        self,
        request: SourceRequest,
        workspace: LectureWorkspace,
        raw_media_path: Path | None,
        *,
        skipped: bool,
    ) -> DownloadResult:
        downloaded_files = [path.resolve() for path in workspace.list_downloaded_files()]
        return DownloadResult(
            request=request,
            lecture_root=workspace.lecture_root.resolve(),
            source_dir=workspace.source_dir.resolve(),
            metadata_path=workspace.metadata_path.resolve(),
            raw_info_path=workspace.raw_info_path.resolve(),
            source_request_path=workspace.source_request_path.resolve(),
            raw_media_path=None if raw_media_path is None else raw_media_path.resolve(),
            skipped=skipped,
            downloaded_files=downloaded_files,
        )

    @staticmethod
    def _create_ydl(options: dict[str, Any]) -> YoutubeDL:
        return YoutubeDL(options)

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    @staticmethod
    def _base_options() -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
