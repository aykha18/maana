# Maana Ingest

`maana-ingest` is the Python ingestion workspace for the Maana platform.

It now implements a governed lecture pipeline that turns long-form source material
into auditable knowledge artifacts instead of opaque generated summaries. The
current path produces annotations, chapter claim bundles, curator review queues,
applied review audit files, and per-chapter commentary artifacts.

## Current Workflow

The implemented lecture path is:

```text
download -> split -> transcribe -> clean -> annotate -> assess
-> knowledge manifest + claim bundles -> curator review
-> applied review audit -> commentary composition
```

Key governed artifacts:

- `claim_bundle.json`: chapter-level governed claims extracted from annotation output
- `manifest.review.json`: curator review queue over claims and ontology candidates
- `manifest.review.applied.json`: audit record of applied review decisions
- `commentary.json` and/or `commentary.md`: composed commentary built from approved claims only, depending on selected export formats

## Requirements

- Python 3.12
- `uv`
- `ffmpeg`

## Quick Start

From `maana-ingest/`:

```bash
uv sync --extra dev
uv run maana --help
```

From the repo root:

```bash
uv run --project maana-ingest maana --help
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

`CANONICAL_REGISTRY_PATH` is required for applying ontology approval decisions
during lecture review.

## Commands

Core pipeline:

```bash
uv run maana --help
uv run maana download <url>
uv run maana split <lecture-path>
uv run maana transcribe <lecture-path>
uv run maana assess <lecture-path>
uv run maana assess <lecture-path> --prepare-knowledge-manifest
uv run maana prepare-lecture-review <knowledge-manifest.json>
uv run maana apply-lecture-review <manifest.review.json>
uv run maana compose-lecture-commentary <knowledge-manifest.json>
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format all
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format json
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format markdown
uv run maana process <url>
```

Poem pilot and ontology review utilities:

```bash
uv run maana resolve-poem-dataset <dataset.json>
uv run maana prepare-poem-review <resolved-dataset.json>
uv run maana append-approved-terms <review.json>
uv run maana materialize-reviewed-poem-dataset <applied-review.json>
```

`append-approved-terms` also writes an audit file alongside the review JSON so
curator decisions remain traceable.

## Interpretation Modes

Claim bundles carry `interpretation_mode` to support finer commentary routing
than `claim_type` alone.

Current default assignments in the lecture path:

- `couplet_detector` -> `literal`
- `persian_detector` -> `literal`
- `quran_detector` -> `comparative`
- `hadith_detector` -> `comparative`
- `poet_detector` -> `comparative`
- `citation_resolver` -> `comparative`, unless overridden by hints

During review, curators can adjust `reviewed_interpretation_mode`. When the
review file is applied:

- approved claims persist the reviewed mode into the governed claim bundle
- rejected, revision-requested, and pending claims keep their original stored mode
- the applied audit file records original, reviewed, and resulting modes separately

## Commentary Composition

Commentary composition only includes claims whose editorial state is `approved`.

By default, `compose-lecture-commentary` exports both JSON and Markdown. Use
repeatable `--format` options to restrict output formats explicitly:

```bash
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format all
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format json
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format markdown
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format json --format markdown
```

The CLI now also reports the selected export formats and prints artifact paths
grouped by chapter so multi-chapter runs are easier to scan.

Optional commentary sections are routed primarily by `interpretation_mode`, with
`claim_type` used as a fallback for legacy or untyped claims.

Current section families include:

- `literal_clarification`
- `descriptive_reading`
- `interpretive_reading`
- `comparative_references`
- `historical_context`
- `synthetic_reflection`

## Documentation

- Workflow reference: [GovernedLectureWorkflow_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/GovernedLectureWorkflow_v1.md)
- Commentary schema: [CanonicalCommentarySchema_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/CanonicalCommentarySchema_v1.md)

## Current Status

The repository is beyond Phase 0 scaffolding. The current implemented baseline includes:

- CLI entrypoints for lecture review and commentary composition
- knowledge manifest and governed chapter claim bundle generation
- curator review queues with ontology decision support
- applied review audit output with interpretation-mode traceability
- per-chapter commentary export generation from approved claims with selectable JSON and Markdown outputs
- commentary CLI output that reports selected export formats and groups artifact paths by chapter
- focused tests for review and commentary routing behavior
