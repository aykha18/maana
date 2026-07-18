# Governed Lecture Workflow v1

## Purpose

This document describes the currently implemented governed lecture pipeline in
`maana-ingest`.

It is an implementation-facing workflow reference, not a replacement for the
broader architectural documents. Its purpose is to make the current artifact
chain, review lifecycle, and commentary composition rules explicit.

## Workflow

The present lecture workflow is:

```text
download
-> split
-> transcribe
-> clean
-> annotate
-> assess
-> knowledge manifest bootstrap
-> claim bundle generation
-> curator review preparation
-> curator review application
-> commentary composition
```

## Governing Principle

Lecture knowledge is governed through claims, not through freeform commentary.

This means:

- claim bundles are the reviewable unit
- curator review is the approval gate
- commentary is composed from governed claims
- commentary must not include unapproved claims
- audit files must preserve what was proposed, reviewed, and applied

## Artifact Chain

The current workflow produces these core artifacts:

| Stage | Artifact | Role |
| --- | --- | --- |
| assessment | `manifest.json` | Tracks chapter readiness and review state |
| claim extraction | `claim_bundle.json` | Stores chapter-level governed claims |
| curator queue | `manifest.review.json` | Queues claim and ontology decisions for human review |
| review apply | `manifest.review.applied.json` | Audits what review decisions were applied |
| commentary | `commentary.json` and/or `commentary.md` | Schema-aligned and human-readable commentary artifacts, depending on selected export formats |

## CLI Sequence

Typical operator sequence:

```bash
uv run maana assess <lecture-path> --prepare-knowledge-manifest
uv run maana prepare-lecture-review <knowledge-manifest.json>
uv run maana apply-lecture-review <manifest.review.json>
uv run maana compose-lecture-commentary <knowledge-manifest.json>
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format all
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format json
uv run maana compose-lecture-commentary <knowledge-manifest.json> --format markdown
```

## Claim Bundle Semantics

Each chapter claim bundle is generated from annotation outputs and carries:

- `claim_id`
- `claim_type`
- `interpretation_mode`
- evidence and provenance records
- ontology candidate mappings
- review metadata

The claim bundle is the source of truth for governed lecture interpretation at
the chapter level.

## Interpretation Mode

`interpretation_mode` refines semantic routing beyond coarse `claim_type`.

Current default assignments in the lecture pipeline are:

| Source analyzer | Default `interpretation_mode` |
| --- | --- |
| `couplet_detector` | `literal` |
| `persian_detector` | `literal` |
| `quran_detector` | `comparative` |
| `hadith_detector` | `comparative` |
| `poet_detector` | `comparative` |
| `citation_resolver` | `comparative` |

These defaults may be overridden by structured annotation hints when available.

## Curator Review Lifecycle

`prepare-lecture-review` builds a chapter-spanning review queue from governed
claim bundles. Each queued item exposes:

- original `interpretation_mode`
- editable `reviewed_interpretation_mode`
- editorial state and truth status
- ontology candidate decisions

`apply-lecture-review` then applies curator decisions back into the governed
artifacts.

Current apply semantics:

- `approve` updates editorial state, truth status, and persists the reviewed interpretation mode
- `reject` updates review state but does not rewrite the stored interpretation mode
- `request_revision` keeps the claim in review and does not rewrite the stored interpretation mode
- `pending` leaves the claim unchanged

The applied audit file records:

- original interpretation mode
- reviewed interpretation mode
- resulting interpretation mode

This preserves traceability when a curator proposes a semantic reclassification
that should not yet affect downstream commentary.

## Commentary Composition Rules

`compose-lecture-commentary` builds per-chapter commentary artifacts from the
knowledge manifest and governed claim bundles.

Current composition rules:

- only claims with editorial state `approved` are included
- source references are preserved in the artifact
- provenance, evidence posture, ontology links, and disagreement markers are surfaced
- optional sections are routed by `interpretation_mode`, with `claim_type` fallback support for legacy claims
- default export writes both JSON and Markdown, with repeatable `--format` options and an `all` alias available to control output
- CLI output reports selected export formats and groups emitted artifact paths by chapter

Current optional section routing:

| Section | Primary `interpretation_mode` values | `claim_type` fallback |
| --- | --- | --- |
| `literal_clarification` | `literal`, `paraphrastic` | `textual` |
| `descriptive_reading` | `descriptive` | `descriptive`, `ontological` |
| `interpretive_reading` | `symbolic`, `emotional`, `psychological`, `existential`, `mystical`, `philosophical` | `interpretive` |
| `comparative_references` | `comparative` | `referential`, `relational` |
| `historical_context` | none | `historical` |
| `synthetic_reflection` | `pedagogical`, `synthetic` | `inferential` |

## Operational Notes

- `CANONICAL_REGISTRY_PATH` must be configured to approve ontology candidates against the registry.
- Commentary composition is intentionally downstream of curator review.
- The current workflow is chapter-scoped even though review and manifest handling operate across a lecture.
- `--format all` is equivalent to requesting both JSON and Markdown explicitly.

## Near-Term Follow-Up

The next likely implementation layer after this workflow is export-oriented polish:

- consider dedicated export commands or presets for downstream consumers
- surface export-format behavior more explicitly in operator-facing docs
- add richer workflow docs for downstream UI and search consumers
