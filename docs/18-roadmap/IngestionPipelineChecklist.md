# Ingestion Pipeline Checklist

This checklist turns [IngestionPipelineTasks.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/IngestionPipelineTasks.md) into ticket-ready implementation work for `Phase 0` through `Phase 4`.

Use this document as the execution checklist for the first delivery track.

## Scope

- Includes `Phase 0` through `Phase 4`
- Targets the first end-to-end MVP path
- Assumes Python 3.12, `uv`, `Typer`, `yt-dlp`, `FFmpeg`, and `faster-whisper`

## Phase 0: Project Foundation

### P0-01 Create ingestion workspace

- [ ] Create the new application workspace, for example `maana-ingest/`
- [ ] Create the initial package layout:
  - `app/`
  - `config/`
  - `core/`
  - `download/`
  - `audio/`
  - `speech/`
  - `annotation/`
  - `ontology/`
  - `storage/`
  - `exporters/`
  - `database/`
  - `models/`
  - `cli/`
  - `tests/`
- [ ] Add package `__init__` files where needed

Acceptance criteria:

- Project folders exist and import cleanly
- Repository has a clear home for all pipeline stages

### P0-02 Initialize Python project with uv

- [ ] Initialize project metadata with `uv`
- [ ] Set Python version target to `3.12`
- [ ] Add base dependencies:
  - `typer`
  - `pydantic-settings`
  - `sqlmodel`
  - `loguru`
  - `yt-dlp`
  - `faster-whisper`
- [ ] Add dev dependencies:
  - `pytest`
  - `pytest-cov`
  - `ruff`
  - `mypy`

Acceptance criteria:

- Dependency metadata is committed
- A fresh environment installs successfully

### P0-03 Add configuration bootstrap

- [ ] Add `.env.example`
- [ ] Define settings for:
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `WHISPER_MODEL`
  - `SEGMENT_LENGTH`
  - `OUTPUT_DIR`
- [ ] Implement config loading with `pydantic-settings`
- [ ] Add config validation for missing required values

Acceptance criteria:

- Application reads config from `.env`
- Invalid or missing config fails with a clear error

### P0-04 Add logging and shared runtime utilities

- [ ] Configure `loguru` logging
- [ ] Add shared path helpers for project data directories
- [ ] Add utilities for run IDs, timestamps, and file naming
- [ ] Add a consistent output directory convention

Acceptance criteria:

- Commands log to console in a consistent format
- Shared utilities can be imported by all stages

### P0-05 Add CLI entrypoint

- [ ] Create a `Typer` app
- [ ] Add root `maana` command
- [ ] Add placeholder subcommands for:
  - `download`
  - `split`
  - `transcribe`
  - `process`
- [ ] Return helpful `--help` output

Acceptance criteria:

- `maana --help` works
- Subcommand help is visible even before full implementation

### P0-06 Add quality tooling

- [ ] Configure `ruff`
- [ ] Configure `mypy`
- [ ] Configure `pytest`
- [ ] Add a minimal smoke test for CLI startup
- [ ] Add developer README for install and local usage

Acceptance criteria:

- Lint, type check, and tests run locally
- New contributors can bootstrap from the README

## Phase 1: Source Intake And Download

### P1-01 Define source request and output models

- [ ] Create input models for source requests
- [ ] Include:
  - source URL
  - source type
  - requested output directory
- [ ] Create output models for downloaded assets and metadata

Acceptance criteria:

- Downloader interface accepts validated input models
- Output schemas are explicit and reusable

### P1-02 Implement deterministic lecture folder layout

- [ ] Define lecture directory naming rules
- [ ] Define locations for:
  - raw source media
  - metadata JSON
  - thumbnails
  - subtitles
  - logs
- [ ] Add slugging and collision-safe naming helpers

Acceptance criteria:

- Repeated runs generate predictable paths
- One lecture’s artifacts are isolated from another’s

### P1-03 Build yt-dlp downloader service

- [ ] Implement download service using `yt-dlp`
- [ ] Download best audio-only source
- [ ] Save raw media to the lecture directory
- [ ] Capture and persist downloader logs

Acceptance criteria:

- A sample YouTube URL downloads successfully
- Downloaded media is saved in the expected directory

### P1-04 Persist source metadata and optional subtitles

- [ ] Persist raw metadata for:
  - title
  - speaker
  - duration
  - upload date
  - YouTube id
  - description
  - thumbnail
  - channel
- [ ] Save subtitles when available
- [ ] Download and persist the thumbnail

Acceptance criteria:

- Metadata JSON is complete for a successful download
- Optional assets are saved when present

### P1-05 Add retry and idempotency behavior to downloads

- [ ] Detect already completed downloads
- [ ] Skip or reuse existing files on rerun
- [ ] Add retry logic for transient download failures
- [ ] Log partial and failed states clearly

Acceptance criteria:

- Rerunning the same URL does not duplicate completed artifacts
- Failures are diagnosable from logs

### P1-06 Expose download command in CLI

- [ ] Implement `maana download <url>`
- [ ] Print output location after success
- [ ] Return non-zero exit codes on failure

Acceptance criteria:

- The command downloads a representative lecture from CLI
- Success and failure behavior are clear to the operator

## Phase 2: Audio Normalization And Segmentation

### P2-01 Add FFmpeg preflight checks

- [ ] Detect whether `ffmpeg` is available
- [ ] Add a clear error message when it is missing
- [ ] Expose version or capability info in logs

Acceptance criteria:

- Missing FFmpeg is detected before processing starts
- Operators get an actionable installation error

### P2-02 Implement audio extraction and normalization

- [ ] Convert source media to WAV
- [ ] Normalize to:
  - mono
  - 16 kHz
  - PCM WAV
- [ ] Save the normalized file in the lecture workspace

Acceptance criteria:

- Any downloaded lecture can produce a normalized WAV
- The output format matches the required transcription input

### P2-03 Add optional silence trimming

- [ ] Implement silence trimming behind a config flag
- [ ] Leave the default behavior conservative
- [ ] Log whether trimming was applied

Acceptance criteria:

- Silence trimming can be enabled or disabled by config
- Default behavior does not damage baseline pipeline stability

### P2-04 Implement fixed-length chapter segmentation

- [ ] Split normalized audio into fixed-length chunks
- [ ] Use `SEGMENT_LENGTH` with default `600` seconds
- [ ] Generate stable filenames for chapter audio files

Acceptance criteria:

- Chapter boundaries are stable across reruns
- Chunk files cover the full normalized audio

### P2-05 Persist chapter manifest

- [ ] Persist chapter metadata:
  - chapter number
  - start
  - end
  - duration
  - file path
- [ ] Validate that manifest records match actual files

Acceptance criteria:

- Chapter manifest JSON exists for each processed lecture
- Manifest entries line up with files on disk

### P2-06 Expose segmentation command in CLI

- [ ] Implement `maana split <lecture-path>`
- [ ] Accept either raw media or normalized audio input, if desired
- [ ] Print chapter output summary after completion

Acceptance criteria:

- CLI can create chapter audio files from a downloaded lecture
- Operator can see where chunk files were written

## Phase 3: Speech Recognition

### P3-01 Build transcription service with faster-whisper

- [ ] Implement transcription service using `faster-whisper`
- [ ] Make model selection configurable
- [ ] Default to `large-v3`

Acceptance criteria:

- The transcription service runs on a chapter audio file
- Model selection is configurable from settings

### P3-02 Add runtime device selection

- [ ] Detect CUDA availability
- [ ] Fall back to CPU when CUDA is unavailable
- [ ] Log selected runtime mode

Acceptance criteria:

- Transcription works on both GPU-capable and CPU-only machines
- Runtime selection is visible in logs

### P3-03 Persist transcription outputs

- [ ] Save:
  - raw JSON
  - plain text
  - SRT
  - VTT
- [ ] Persist per-segment timestamps
- [ ] Persist confidence where available

Acceptance criteria:

- Each processed chapter produces the expected output formats
- Structured outputs preserve timing information

### P3-04 Add transcription progress and retry behavior

- [ ] Show progress for long-running transcription jobs
- [ ] Retry failed chapters without rerunning successful chapters
- [ ] Mark incomplete chapters clearly in state or logs

Acceptance criteria:

- Operators can monitor progress during transcription
- Failed chapters can be retried independently

### P3-05 Expose transcription command in CLI

- [ ] Implement `maana transcribe <lecture-path>`
- [ ] Support processing all chapter files for a lecture
- [ ] Print output summary after completion

Acceptance criteria:

- CLI can transcribe a representative lecture end to end
- Outputs are created for every available chapter

## Phase 4: Transcript Cleaning

### P4-01 Define cleaned transcript schema

- [ ] Define a schema that preserves:
  - original segment text
  - cleaned text
  - timestamps
  - chapter identity
- [ ] Separate raw transcription records from cleaned transcript records

Acceptance criteria:

- Cleaning stage has a clear, typed contract
- Timestamps remain available after cleaning

### P4-02 Implement punctuation and script normalization

- [ ] Add normalization rules for Urdu punctuation
- [ ] Add normalization rules for Persian punctuation
- [ ] Add normalization rules for Arabic punctuation
- [ ] Make normalization behavior deterministic

Acceptance criteria:

- Known punctuation normalization cases pass consistently
- Repeated runs produce identical cleaned output

### P4-03 Merge broken sentence fragments safely

- [ ] Identify obvious sentence fragments caused by ASR segmentation
- [ ] Merge fragments only when confidence is high
- [ ] Preserve mapping back to source timestamps

Acceptance criteria:

- Cleaning improves readability without losing source alignment
- Merge rules avoid aggressive rewriting

### P4-04 Export cleaned transcript artifacts

- [ ] Export `clean_transcript.md`
- [ ] Export `transcript.json`
- [ ] Save outputs in the lecture workspace with deterministic names

Acceptance criteria:

- Cleaned transcript outputs are generated for processed lectures
- Human-readable and machine-readable artifacts are both available

### P4-05 Add normalization and cleaning tests

- [ ] Add unit tests for punctuation normalization
- [ ] Add tests for timestamp preservation
- [ ] Add tests for sentence merge behavior
- [ ] Add at least one fixture-based cleaning test from a representative lecture sample

Acceptance criteria:

- Cleaning logic has focused automated coverage
- Core normalization rules are protected against regression

### P4-06 Expose cleaning command or stage integration

- [ ] Add a dedicated cleaning command or integrate cleaning into a process flow
- [ ] Print output locations after success
- [ ] Return clear failures for invalid transcription input

Acceptance criteria:

- Operators can run transcript cleaning without manual file juggling
- Cleaning stage fits cleanly into the future `process` pipeline

## Suggested Execution Order

- [ ] Complete all `Phase 0` tickets
- [ ] Complete `P1-01` through `P1-06`
- [ ] Complete `P2-01` through `P2-06`
- [ ] Complete `P3-01` through `P3-05`
- [ ] Complete `P4-01` through `P4-06`

## MVP Gate For Phase 0 Through Phase 4

- [ ] `maana download <url>` works on a representative lecture
- [ ] `maana split <lecture-path>` produces normalized audio and chapters
- [ ] `maana transcribe <lecture-path>` produces JSON, text, SRT, and VTT
- [ ] Cleaning produces `clean_transcript.md` and `transcript.json`
- [ ] The system is rerunnable without duplicating completed work
- [ ] Logs and test coverage are good enough to begin orchestration work
