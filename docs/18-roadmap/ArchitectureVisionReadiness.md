# Architecture Vision Readiness

This document translates `docs/Architecture_Vision` into an execution gate for the current codebase.

## Current Verdict

- The current project is strong for lecture artifact acquisition and preprocessing.
- The current project is not yet optimized for the full ontology-first Ma'na architecture.
- We can start controlled source ingestion now.
- We should not start canonical knowledge ingestion yet.
- Curator UI is not implemented and remains a hard blocker for canonical approval workflows.

## What Is Ready

- Source preservation is implemented:
  - download request
  - raw media
  - raw metadata
  - deterministic lecture workspace
- Audio preparation is implemented:
  - normalization
  - fixed chaptering
  - manifests
- Transcript generation is implemented:
  - JSON
  - TXT
  - SRT
  - VTT
- Transcript cleaning is implemented with deterministic normalization rules.
- Specialized annotation infrastructure is implemented with provider-aware clients and structured JSON outputs.

## What Is Missing

- Canonical ontology runtime layer
- Canonical registry persistence and lookup
- Extraction schemas for:
  - themes
  - symbols
  - concepts
  - human experiences
  - vocabulary
  - commentary
  - literary devices
- Ontology mapping rules that prefer existing canonical entities
- Provenance validation for all extracted claims
- Curator review actions:
  - approve
  - reject
  - merge
  - split
  - rename
  - create new
- Curator UI
- Reader UI
- API/backend for curator and reader applications
- Durable storage split across structured data, embeddings, graph, and source asset storage

## Ingestion Decision

Use two separate decisions instead of one:

1. Artifact ingestion

- Status: yes
- Meaning: downloading lectures, preserving originals, splitting audio, transcribing, cleaning, and generating structured annotation proposals

2. Canonical knowledge ingestion

- Status: no
- Meaning: promoting extracted entities into the Ma'na ontology or knowledge graph

## Required Gates Before Canonical Ingestion

1. Phase 6A: Ontology foundation
- Add knowledge extraction schemas and a dedicated `knowledge/` workspace area.
- Add a canonical registry contract and registry file.
- Add lecture readiness checks that explicitly gate canonical ingestion.

2. Phase 6B: Extraction and mapping
- Extract themes, symbols, concepts, human experiences, vocabulary, commentary, and literary devices into structured chapter outputs.
- Separate extraction from ontology resolution.
- Require provenance for every extracted claim.

3. Phase 6C: Curator workflow backend
- Persist proposed entities, mapping decisions, and review states.
- Support merge, split, rename, approve, reject, and create-new actions.

4. Phase 6D: Curator UI
- Build a review queue for chapters and proposed entities.
- Show evidence snippets with timestamps.
- Support canonical match selection and new entity creation.

## Immediate Execution Order

1. Keep source ingestion running only as artifact acquisition.
2. Add Phase 6 foundations in code:
   - ontology models
   - readiness assessment
   - knowledge manifest bootstrap
3. Create a canonical registry seed file.
4. Implement extractor outputs for the missing ontology object families.
5. Implement curator backend state and review APIs.
6. Implement Curator UI before approving any canonical entities.

## Definition Of Ready

Canonical knowledge ingestion is ready only when all of the following are true:

- cleaned transcript exists
- annotation manifest exists
- canonical registry is configured
- provenance-aware knowledge manifest exists
- curator workflow exists
- curator UI exists
- extracted entities can be approved without mutating source artifacts
