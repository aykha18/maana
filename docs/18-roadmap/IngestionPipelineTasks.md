# Ingestion Pipeline Tasks

This document turns [Ingestion-pipeline.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/Ingestion-pipeline.md) into an implementation plan that can be executed in phases.

The goal is to build a production-grade Python ingestion service that converts long-form audio or video lectures into structured Maana knowledge artifacts.

## Delivery Principles

- Build the smallest end-to-end pipeline first.
- Keep the system offline-first except for LLM annotation.
- Make every stage idempotent and resumable.
- Prefer structured outputs between stages over loose text files.
- Keep ontology definitions in `04-ontology/` and only reference them here.
- Treat YouTube as the first source, not the final boundary.

## Recommended MVP Boundary

The first shippable version should do the following:

1. accept a YouTube URL
2. download source media and metadata
3. normalize audio
4. split audio into fixed-length chapters
5. transcribe with `faster-whisper`
6. clean and persist the transcript
7. export chapter markdown and JSON

Do not block MVP on:

- semantic chaptering
- FastAPI or React UI
- graph database export
- advanced source support beyond YouTube
- highly specialized literary analyzers

## Phase 0: Project Foundation

### Objective

Create the repository skeleton, local developer workflow, and core runtime conventions.

### Tasks

- Create a new Python application workspace, for example `maana-ingest/`.
- Initialize project metadata with `uv`.
- Add base dependencies:
  - `typer`
  - `pydantic-settings`
  - `sqlmodel`
  - `loguru`
  - `yt-dlp`
  - `faster-whisper`
- Add dev dependencies:
  - `pytest`
  - `pytest-cov`
  - `ruff`
  - `mypy`
- Define the top-level package structure from the ingestion spec:
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
- Add `.env.example` with the required settings.
- Add project logging, config loading, and path management utilities.
- Add a single CLI entrypoint such as `maana`.
- Add a README for the ingestion app with install and run steps.

### Deliverables

- Runnable Python project scaffold
- `uv` environment
- CLI bootstrap command
- lint and type-check config

### Exit Criteria

- `maana --help` works
- config loads from `.env`
- linting and tests run locally

## Phase 1: Source Intake And Download

### Objective

Support intake of a YouTube URL and persist source artifacts plus metadata.

### Tasks

- Implement an input model for source requests:
  - source URL
  - source type
  - requested output directory
- Implement `yt-dlp` downloader service.
- Download best audio-only source.
- Persist raw metadata:
  - title
  - speaker
  - duration
  - upload date
  - YouTube id
  - description
  - thumbnail
  - channel
- Save subtitles if they exist.
- Store raw source files in a deterministic directory layout.
- Add retry handling and failure logging for download operations.
- Add CLI command:
  - `maana download URL`

### Deliverables

- Download service
- metadata JSON
- raw source asset directory

### Exit Criteria

- A sample YouTube lecture downloads successfully
- output folder structure is deterministic
- rerunning the same command does not duplicate completed artifacts

## Phase 2: Audio Normalization And Segmentation

### Objective

Produce clean WAV audio and chapter-level chunks ready for transcription.

### Tasks

- Add FFmpeg preflight checks.
- Implement audio extraction to WAV.
- Normalize to:
  - mono
  - 16 kHz
  - PCM WAV
- Add optional silence trimming behind a config flag.
- Implement first-pass segmentation using fixed-length chunks, default `600` seconds.
- Persist chapter metadata:
  - chapter number
  - start
  - end
  - duration
  - file path
- Add CLI commands:
  - `maana split lecture.mp3`
  - or an equivalent chaptering command over normalized audio

### Deliverables

- normalized audio file
- chapter audio files
- chapter manifest JSON

### Exit Criteria

- Any downloaded lecture can be normalized
- chapter boundaries and filenames are stable across reruns
- chapter manifests line up with actual files on disk

## Phase 3: Speech Recognition

### Objective

Transcribe chapter audio into structured machine-readable outputs.

### Tasks

- Implement `faster-whisper` transcription service.
- Support configurable model selection with default `large-v3`.
- Detect whether CUDA is available and fall back to CPU.
- Persist transcription outputs:
  - raw JSON
  - plain text
  - SRT
  - VTT
- Store per-segment timestamps and confidence where available.
- Add CLI command:
  - `maana transcribe lecture.mp3`
- Add progress reporting for long-running jobs.

### Deliverables

- chapter transcription outputs
- transcription manifest

### Exit Criteria

- A sample lecture transcribes end to end
- outputs are produced for all chapter files
- a failed chapter can be retried without rerunning completed chapters

## Phase 4: Transcript Cleaning

### Objective

Transform raw ASR output into a cleaned transcript suitable for annotation and reading.

### Tasks

- Design a transcript schema that preserves:
  - original segment text
  - cleaned text
  - timestamps
  - chapter identity
- Implement text normalization rules for Urdu, Persian, and Arabic punctuation.
- Merge obviously broken sentence fragments where safe.
- Preserve alignment between cleaned text and source timestamps.
- Export:
  - `clean_transcript.md`
  - `transcript.json`
- Add automated tests for normalization rules.

### Deliverables

- transcript cleaning module
- cleaned transcript outputs
- normalization tests

### Exit Criteria

- cleaned output remains timestamp-aware
- normalization is deterministic
- test cases cover common transcription cleanup patterns

## Phase 5: Annotation Architecture

### Objective

Build the annotation layer as specialized analyzers instead of a single fragile prompt.

### Tasks

- Define the annotation contract for all analyzers.
- Create provider-agnostic LLM client configuration:
  - OpenAI
  - OpenRouter
  - Ollama
  - Anthropic
  - Gemini
- Implement base annotation pipeline over cleaned chapter transcripts.
- Build specialized analyzers:
  - `couplet_detector.py`
  - `quran_detector.py`
  - `hadith_detector.py`
  - `poet_detector.py`
  - `persian_detector.py`
  - `citation_resolver.py`
- Add a merger stage that combines analyzer outputs into one structured chapter result.
- Add prompt versioning and prompt storage for repeatability.
- Add mockable interfaces so tests do not depend on live LLM calls.
- Add CLI command:
  - `maana annotate lecture/`

### Deliverables

- annotation client abstraction
- specialized analyzers
- merged annotation schema

### Exit Criteria

- a chapter can be annotated with a configurable provider
- each analyzer produces structured JSON
- annotation results can be replayed and compared across prompt versions

## Phase 6: Ontology Mapping And Knowledge Extraction

### Objective

Convert transcript and annotation output into Maana-compatible structured knowledge.

### Tasks

- Define extraction schemas for:
  - summary
  - detailed explanation
  - vocabulary
  - couplets
  - references
  - commentary
  - themes
- Map extracted themes, symbols, concepts, and experiences to existing ontology terms.
- Add validation rules that reject non-canonical ontology values unless explicitly flagged.
- Separate extraction from ontology resolution so both can evolve independently.
- Add vocabulary extraction fields:
  - word
  - language
  - root
  - meaning
  - usage
  - etymology
- Add provenance to every extracted claim:
  - source chapter
  - timestamps
  - detector or prompt origin

### Deliverables

- extraction schema definitions
- ontology resolver
- provenance-aware structured JSON

### Exit Criteria

- extracted entities reference canonical ontology terms where applicable
- provenance exists for major outputs
- invalid ontology mappings are surfaced clearly

## Phase 7: Exporters And Persistence

### Objective

Save the processed lecture in formats useful for editorial review and downstream systems.

### Tasks

- Implement markdown exporter for per-chapter outputs.
- Implement JSON exporter for machine consumption.
- Define SQLite schema for:
  - lectures
  - chapters
  - segments
  - vocabulary
  - poets
  - poems
  - couplets
  - themes
  - concepts
  - symbols
  - commentary
- Add persistence services using `SQLModel`.
- Persist run metadata, stage status, timestamps, and errors.
- Add support for export bundles per lecture.
- Leave graph export as a second-pass task after JSON stability.
- Add CLI command:
  - `maana export lecture/`

### Deliverables

- markdown exporter
- JSON exporter
- SQLite persistence layer

### Exit Criteria

- one processed lecture can be exported to markdown and JSON
- SQLite stores run and content records cleanly
- outputs are readable by both humans and downstream services

## Phase 8: Pipeline Orchestration

### Objective

Connect all stages into a resumable end-to-end process command.

### Tasks

- Create a pipeline runner that tracks stage state.
- Add resumable execution per lecture.
- Add stage-level retries and failure summaries.
- Add CLI command:
  - `maana process URL`
- Support stage skipping for development, for example:
  - `--from-stage`
  - `--to-stage`
  - `--force`
- Write a run manifest that records:
  - stage durations
  - outputs
  - failures
  - retries

### Deliverables

- orchestration service
- process command
- resumable run metadata

### Exit Criteria

- the full pipeline runs from URL to exported outputs
- interrupted runs can resume from the last valid stage
- stage status is transparent from logs and persisted state

## Phase 9: Quality, Testing, And Ops

### Objective

Make the pipeline reliable enough for repeated use and future deployment.

### Tasks

- Add unit tests for downloader, audio utilities, cleaning, exporters, and config.
- Add integration tests for the MVP pipeline using fixture media.
- Add mocked tests for LLM annotation and whisper boundaries where needed.
- Add static checks:
  - `ruff`
  - `mypy`
  - `pytest`
- Add Docker support:
  - `Dockerfile`
  - `docker-compose.yml`
  - volume strategy
  - optional GPU profile
- Add documentation for local setup, FFmpeg installation, and model/runtime requirements.
- Add operational logging and error codes for each pipeline stage.

### Deliverables

- test suite
- Docker setup
- operator documentation

### Exit Criteria

- a fresh developer machine can run the pipeline from docs alone
- CI can run static checks and test suite
- common failures are diagnosable from logs and persisted run status

## Phase 10: Post-MVP Extensions

These should follow only after the MVP path is stable.

- semantic chapter detection
- Neo4j, GraphML, or NetworkX graph export
- FastAPI backend
- React frontend
- pipeline status dashboard
- support for local audio, podcasts, and additional sources
- task queue and asynchronous execution
- object storage support such as S3 or MinIO

## Immediate Execution Order

If implementation starts now, use this order:

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 7 markdown and JSON export only
7. Phase 8
8. Phase 9 baseline tests and Docker
9. Phase 5 specialized annotation
10. Phase 6 ontology mapping
11. Phase 7 database persistence expansion

This order gets an end-to-end artifact quickly, then hardens and enriches it.

## First Sprint Suggestion

The first sprint should produce a working command chain for one lecture:

- scaffold the Python app
- wire configuration and logging
- implement YouTube download
- normalize audio with FFmpeg
- chunk audio by fixed length
- transcribe with `faster-whisper`
- export one chapter markdown and one lecture JSON summary

## Definition Of Done For MVP

The MVP is complete when all of the following are true:

- `maana process <youtube-url>` works on a representative sample lecture
- the run is resumable after interruption
- chapter transcripts and cleaned outputs are persisted
- markdown and JSON exports are generated
- logs make failures diagnosable
- tests cover the critical happy path and key failure paths
