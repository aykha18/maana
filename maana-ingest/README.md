# Maana Ingest

`maana-ingest` is the Python ingestion workspace for the Maana platform.

It provides the foundational CLI and runtime scaffolding for a production-grade
pipeline that will convert long-form lectures into structured knowledge assets.
It now also includes an early poem-pilot resolution lane for canonical ontology testing.

## Planned Scope

The first delivery track covers:

- source intake and download
- audio normalization and segmentation
- speech recognition
- transcript cleaning

## Requirements

- Python 3.12
- `uv`
- `ffmpeg`

## Quick Start

```bash
uv sync --extra dev
uv run maana --help
```

## Configuration

Copy `.env.example` to `.env` and adjust settings as needed.

Key settings:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `WHISPER_MODEL`
- `SEGMENT_LENGTH`
- `CANONICAL_REGISTRY_PATH`
- `OUTPUT_DIR`

## Commands

```bash
uv run maana --help
uv run maana download <url>
uv run maana split <lecture-path>
uv run maana transcribe <lecture-path>
uv run maana assess <lecture-path>
uv run maana resolve-poem-dataset <dataset.json>
uv run maana prepare-poem-review <resolved-dataset.json>
uv run maana append-approved-terms <review.json>
uv run maana materialize-reviewed-poem-dataset <applied-review.json>
uv run maana process <url>
```

`append-approved-terms` also writes an audit file alongside the review JSON so curator decisions remain traceable.

## Current Status

Phase 0 scaffolding is in place:

- project metadata
- config bootstrap
- logging setup
- CLI entrypoint
- smoke test
