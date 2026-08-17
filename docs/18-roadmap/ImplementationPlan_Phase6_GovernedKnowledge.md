# Phase 0: Semantic Infrastructure — 2-Week Sprint

## Purpose

Build the semantic engine that makes Ma'ana self-organizing.

The objective is not merely to "put existing concepts into a database."
The objective is to build a system in which:

> **adding a new World automatically makes Ma'ana smarter about all existing Worlds.**

## Scope

Phase 0 covers:
- Semantic data model (World, Chapter, Part, SemanticCluster, WordFamily, Relation)
- PostgreSQL + pgvector schema
- Neo4j graph schema
- Canonical World JSON schema
- Relation taxonomy
- Multiple typed embeddings per World
- Semantic projection service
- Agent system (Ingestion, Relation, Architect, Ring, Gap, Quality)
- API for semantic operations
- Human-in-the-loop approval workflow

Phase 0 does not cover:
- Literary ingestion pipeline
- Commentary composition
- Reader application
- Curator application (semantic curator only)

## Architecture Principle

**PostgreSQL = canonical truth**
**Neo4j = semantic relationships**
**Vector index = semantic proximity**

Do not make the vector database the source of truth.
Do not make the GraphDB the source of truth either.
The canonical Ma'na object lives in PostgreSQL.

## Week 1: Foundation

### Day 1: Freeze the Semantic Data Model

Create core entities:
- World
- Chapter
- Part
- SemanticCluster
- WordFamily
- Relation
- Poet
- Theme
- Symbol
- Source
- Citation
- WorldVersion
- Embedding
- SemanticAnalysis
- ArchitectureSnapshot

### Day 2: Design the Relationship Model

Define explicit relationship types:

Hierarchical: PART_OF, CONTAINS, BELONGS_TO
Semantic: RELATED_TO, CONTRASTS_WITH, OPPOSITE_OF, DEEPENS, PRECEDES, FOLLOWS, EXPANDS
Linguistic: WORD_FAMILY, DERIVED_FROM, SYNONYM_OF, NEAR_SYNONYM_OF, ANTONYM_OF
Literary: USED_BY, DEVELOPED_BY, SYMBOLIZED_BY, THEME_OF
Architectural: SEMANTIC_BRIDGE, RING_LINK, CHAPTER_ANCHOR, CLUSTER_ANCHOR, TRANSITION_TO

### Day 3: PostgreSQL + pgvector

Tables: worlds, chapters, parts, clusters, word_families, relations, poets, themes, symbols, sources, citations, world_versions, embeddings, semantic_analysis, architecture_snapshots, agent_runs, agent_proposals.

Create multiple semantic representations per World:
- embedding_full
- embedding_definition
- embedding_meaning
- embedding_literary
- embedding_philosophical
- embedding_modern
- embedding_questions

### Day 4: Build the Canonical World JSON

Every World should have a machine-readable representation.

### Day 5: Import Existing Worlds

Build an ingestion pipeline:
```
Existing Markdown
  ↓
Parser
  ↓
World JSON
  ↓
Validator
  ↓
PostgreSQL
  ↓
Embedding Generator
  ↓
Graph Projection
```

Each imported World receives:
- stable world_id
- version = 1
- source = legacy_maana
- migration_status

Preserve original Markdown. Never destroy original material.

### Day 6: Build Neo4j

Graph structure example:
```
(خیال)
   │
   ├──PRECEDES──>(تصور)
   ├──RELATED_TO──>(عشق)
   ├──EXPANDS──>(معنی)
   ├──USED_BY──>(Rumi)
   └──CONTRASTS_WITH──>(جمود)
```

### Day 7: Synchronization Layer

Build the Semantic Projection Service.

Whenever a World changes:
```
Postgres
  ├──► regenerate embeddings
  └──► update GraphDB
```

Events: WORLD_CREATED, WORLD_UPDATED, WORLD_RELATION_CHANGED, WORLD_DELETED.

## Week 2: Intelligence Layer

### Day 8: Semantic Ingestion Agent

Input: New World proposal
Agent determines: definition, word family, themes, related worlds, opposites, literary dimensions, potential chapter, potential cluster.

Agent must NOT automatically modify the canonical graph. Instead:
```
Agent
  ↓
Proposal
  ↓
Validation
  ↓
Human approval
  ↓
Canonical DB
```

### Day 9: Relation Discovery Agent

Two-stage architecture:
1. Vector retrieval — find top 20-50 candidates
2. LLM semantic reasoning — evaluate and classify relations

### Day 10: Architect Agent

Input: New World + Current Graph + Current Chapters + Current Clusters
Output: recommended chapter, recommended cluster, relationships, architectural changes, potential reordering, confidence

Questions answered:
1. Where does the new World belong?
2. Does it create a missing connection?
3. Does it expose a weakness in an existing chapter?
4. Should another World move?
5. Does a new semantic cluster need to exist?
6. Does the chapter's central question remain valid?

### Day 11: Ring Agent

Evaluate each chapter as a semantic topology:
- Opening Anchor
- Semantic Progression
- Intermediate Worlds
- Transformation
- Closing Anchor
- Connection to Opening

Produce:
- Ring Score
- Coherence
- Progression
- Redundancy
- Missing bridge
- Weak transition

### Day 12: Gap Detection Agent

Three signals:
1. Graph holes — A ───── C, B is likely missing
2. Vector clusters — dense semantic regions with missing intermediaries
3. Literary corpus — recurring concepts in ingested works that don't have Worlds

### Day 13: Quality & Provenance Agent

Distinguish content types:
- AUTHENTICATED_QUOTE
- PARAPHRASE
- INTERPRETATION
- AI_GENERATED_EXAMPLE
- EDITORIAL_SYNTHESIS

Never mix these.

### Day 14: Build the Ma'na Semantic Engine API

Endpoints:
- POST /worlds
- GET /worlds/{id}
- GET /worlds/{id}/related
- GET /worlds/{id}/path
- GET /worlds/{id}/graph
- GET /chapters/{id}
- GET /chapters/{id}/architecture
- POST /semantic/analyze
- POST /semantic/propose-relations
- POST /semantic/review
- GET /gaps
- GET /architecture/proposals
- GET /architecture/history
- POST /worlds/{id}/architect

## Human-in-the-Loop

Do not recommend:
```
Add World
  ↓
AI automatically restructures Ma'ana
```

Instead:
```
Add World
  ↓
AI analyzes
  ↓
AI proposes
  ↓
Human reviews
  ↓
Approve / Reject / Modify
  ↓
Graph changes
```

Automatic (no approval needed):
- embeddings
- duplicate detection
- related-world suggestions
- vector indexing
- graph synchronization

Human approval required:
- chapter movement
- chapter splitting
- new semantic cluster
- canonical relation
- deletion
- structural redesign

## Scaling Principles

At 10,000 worlds:
- Vector search: 10,000 embeddings → ANN index → Top 30 → LLM reasoning
- Graph: Neo4j handles 10,000 nodes, 100,000+ relationships comfortably
- PostgreSQL: trivial for 10,000 Worlds + versions + sources + metadata

## Architectural Law

```
MA'ANA ARCHITECTURAL LAW

The sequence of Worlds is not the source of truth.
The semantic graph is the source of truth.
Chapters are interpretations of the graph.
World numbers are identifiers, not semantic positions.
No AI agent may silently mutate canonical architecture.
Every structural change must be explainable, versioned, and reversible.
```

## Phase 0 Deliverables

### Foundation
- [ ] PostgreSQL schema
- [ ] pgvector
- [ ] Neo4j instance
- [ ] Neo4j graph schema
- [ ] Canonical World JSON schema
- [ ] Relation taxonomy
- [ ] Versioning system
- [ ] Source/provenance model

### Migration
- [ ] Existing Worlds imported
- [ ] Existing chapters imported
- [ ] Existing relationships extracted
- [ ] Embeddings generated
- [ ] Initial graph generated

### Intelligence
- [ ] Ingestion agent
- [ ] Relation discovery agent
- [ ] Architect agent
- [ ] Ring agent
- [ ] Gap detection agent
- [ ] Quality/provenance agent

### APIs
- [ ] World CRUD
- [ ] Semantic search
- [ ] Related worlds
- [ ] Graph traversal
- [ ] Semantic paths
- [ ] Architecture analysis
- [ ] Agent proposals
- [ ] Approval workflow

### Safety
- [ ] Human approval
- [ ] Architecture snapshots
- [ ] Agent audit logs
- [ ] Rollback
- [ ] Confidence scores
- [ ] Provenance tracking

## Validation

After Phase 0, ingest World 106 — خیال and World 107 — تصور again.
Then introduce استعارہ.
The engine should produce:
- Candidate chapter placement
- Strong relationships to existing Worlds
- Architectural observations about chapter structure
- Ring score improvement

That is the moment the Ma'na Semantic Engine is actually working.

---

# Phase 6: Governed Knowledge Layer — Implementation Plan

## Purpose

This document is the execution plan for Phase 6 of the Ma'na implementation.

It translates the architecture vision, domain model, and roadmap into concrete build steps, deliverables, and validation criteria.

Phase 6 transforms Ma'na from an artifact ingestion pipeline into a governed knowledge platform.

## Scope

Phase 6 covers:

- Governed claim models
- Evidence and provenance capture
- Ontology proposal workflow
- Curator backend
- Commentary composition for one or two scopes
- Reader retrieval over approved knowledge

Phase 6 does not cover:

- Broad public reader application
- Large-scale graph exploration
- Generalized multi-source ingestion beyond controlled pilots
- Collaborative scholar tooling
- Advanced multilingual reasoning

## Current State Assessment

The current repository (`maana-ingest`) is strongest in:

- Source preservation (download, workspace layout, artifact staging)
- Audio preparation (normalization, chaptering, manifests)
- Transcript generation (JSON, TXT, SRT, VTT)
- Transcript cleaning (deterministic normalization rules)
- Specialized annotation infrastructure (provider-aware clients, structured JSON outputs)

The current repository is not yet:

- Emitting governed claim bundles instead of freeform annotations
- Persisting ontology decisions with review state
- Supporting curator approval workflows
- Composing commentary from governed claims
- Serving reader retrieval over approved knowledge

## Implementation Principle

Do not throw away the current ingestion pipeline.

Do not pretend it is already the full architecture.

Instead:

- Preserve what is already strong
- Insert governance boundaries where meaning begins
- Converge lecture and poem ingestion into shared knowledge objects
- Delay full reader experience until knowledge governance is real

## Phase 6 Milestones

### Milestone 6.1: Governed Claim Foundation

Deliver:

- `Claim` domain model with scope, type, and status
- `Evidence` domain model with anchor and source reference
- `ProvenanceRecord` domain model with contributor, method, timestamp, and review history
- `ReviewState` enum and lifecycle model
- Lecture and poem candidate claim emission in unified shape
- Knowledge manifest schema v1

Validation:

- All current annotation outputs can be converted into claim candidates
- Every claim candidate carries evidence anchor and provenance
- No canonical state can be mutated without review

### Milestone 6.2: Ontology Governance

Deliver:

- `OntologyEntity` domain model (theme, symbol, concept, human experience, literary device, question)
- `OntologyProposal` model for proposed new entities and mappings
- `CanonicalRegistry` with lookup, alias, and merge lineage
- Ontology mapping rules that prefer existing canonical entities
- Provider-agnostic extraction schemas for all ontology object families

Validation:

- AI proposals attempt canonical lookup before proposing new entities
- Ontology mappings require curator approval before entering canonical state
- Registry supports merge, split, rename, deprecate, and alias operations

### Milestone 6.3: Curator Backend

Deliver:

- Review queue service
- Proposal lifecycle endpoints (propose, approve, reject, merge, split, rename)
- Version history for all governed objects
- Evidence inspection endpoints
- Provenance validation middleware
- Commentary approval workflow

Validation:

- Curator can approve or reject knowledge objects with evidence visibility
- All approvals produce immutable version history
- Reversibility is preserved for all governance actions

### Milestone 6.4: Commentary Composition

Deliver:

- `CommentaryDocument` composition service
- Unit commentary artifact schema
- Work commentary artifact schema
- Provenance-aware render pipeline
- Commentary versioning and approval lifecycle

Validation:

- Commentary can be generated from governed claim sets
- Commentary preserves linkage to claims, evidence, and sources
- Commentary is distinguishable from source material

### Milestone 6.5: Reader Retrieval

Deliver:

- Question-to-commentary retrieval endpoint
- Source evidence retrieval endpoint
- Ontology traversal endpoint
- Graph traversal endpoint
- Semantic retrieval endpoint (vector search over approved artifacts)
- Retrieval composition layer

Validation:

- Reader can ask a question and receive approved commentary plus source anchoring
- Reader can navigate through linked ontology entities
- Reader sees uncertainty or contested status where relevant
- Semantic retrieval proposes candidates; governed layers determine meaning

## System Boundaries

### Ingestion Boundary

Responsible for turning raw sources into structured candidate artifacts.

Includes: download, import, transcription, cleaning, segmentation, analyzer execution.

Must output: preserved source artifacts, addressable units, candidate claim bundles, provenance-bearing intermediate artifacts.

Must not do: silently canonicalize mappings, silently finalize commentary.

### Knowledge Extraction Boundary

Responsible for converting cleaned transcript or poem text into candidate claims and draft commentary structures.

Includes: vocabulary extraction, theme and human experience proposals, symbolic and concept proposals, commentary claim generation, source anchoring.

Must not do: silently canonicalize mappings, silently finalize commentary.

### Governance Boundary

Responsible for: proposal queues, review states, ontology decisions, version history, approval scope, reversibility.

This is the true heart of Ma'na after ingestion.

### Commentary Boundary

Responsible for composing governed commentary artifacts from approved or scoped claim sets.

### Retrieval Boundary

Responsible for: source retrieval, commentary retrieval, ontology traversal, graph traversal, semantic retrieval using governed stores rather than bypassing them.

## Datastore Responsibility Plan

### 1. Source Preservation Layer

Use for: original media, downloaded sources, OCR outputs, imported texts, transcripts, derived document artifacts, commentary files.

Near-term reality: local workspace already approximates this layer.

### 2. Structured Governance Layer

Use for: works, witnesses, units, claims, evidence, provenance, workflow states, versions, approvals.

Near-term recommendation: start with one structured operational store before introducing full distributed complexity.

### 3. Ontology/Graph Layer

Use for: ontology entities, aliases, semantic relations, graph traversal edges, merge and deprecation lineage.

Near-term recommendation: keep graph scope small and governed first. Do not attempt full graph saturation immediately.

### 4. Vector Store

Use for: embeddings, retrieval chunks, semantic recall.

Near-term recommendation: only embed approved or explicitly scoped artifacts. Do not embed raw experimental output as if it were stable knowledge.

## First Curator Workflow Scope

The first curator product should focus on the highest-value review actions only.

### Curator MVP Scope

- Review proposed ontology mappings
- Review proposed new ontology entities
- Review unit-level commentary claim bundles
- Approve or reject claim sets for limited scope
- Inspect source evidence
- Inspect provenance and AI involvement
- Merge duplicate ontology proposals
- Create or approve canonical mappings

### Curator MVP Must Show

- Source snippet or evidence snippet
- Addressed unit or work
- Proposed ontology target
- Evidence posture
- Contributor and AI provenance
- Current status
- Prior related decisions

### Curator MVP Can Delay

- Full visual graph editing
- Large-scale bulk moderation
- Advanced collaborative editorial discussion
- Rich manuscript comparison tooling

## First Reader Retrieval Scope

The first reader experience should prove the value of governed knowledge, not merely search over raw text.

### Reader MVP Scope

- Ask a question
- Retrieve approved commentary
- Retrieve supporting source passage
- Retrieve linked ontology entities
- Retrieve related works or units through governed relations

### Reader MVP Must Show

- Explanation
- Source anchoring
- Uncertainty or contested status where relevant
- Related concepts and human experiences
- Path to original source material

### Reader MVP Must Avoid

- Pretending unresolved material is final truth
- Flattening all traditions into one answer
- Hiding whether the answer is sourced, interpreted, or synthesized

## Build Sequence

### Step 1. Stabilize Artifact Ingestion As Upstream Infrastructure

Keep the existing lecture ingestion pipeline working.

Do not keep expanding it blindly.

Focus on making it a reliable upstream source-preservation and candidate-generation engine.

### Step 2. Introduce Governed Claim Models

Add first-class models for:

- Claim candidate
- Evidence anchor
- Provenance record
- Review state
- Approval scope

This is the most important code transition.

### Step 3. Convert Annotation And Poem Resolution Outputs Into Claim Bundles

Refactor current outputs so lecture and poem pipelines emit the same governed intermediate shape.

### Step 4. Build Curator Backend First

Before a full UI, create the backend structures for:

- Review queue items
- Decisions
- Version history
- Ontology proposal lifecycle
- Commentary approval lifecycle

### Step 5. Build Curator UI For Review-Critical Actions

Implement the smallest useful curator workflow around:

- Ontology proposals
- Claim approval
- Evidence inspection
- Commentary promotion

### Step 6. Generate Canonical Commentary Artifacts

Create commentary composition from governed claim sets using the new schema.

### Step 7. Build Reader Retrieval Over Approved Knowledge

Only after the approval path exists should the first reader retrieval surface be built.

### Step 8. Add Hybrid Persistence Beyond Local Files

Introduce the structured operational store, then vector and graph layers in limited governed scope.

## Codebase Implications

For the current `maana-ingest` codebase:

### Keep

- Downloader
- Workspace layout discipline
- Audio preparation
- Transcription
- Cleaning
- Annotation analyzers
- Readiness checks
- Poem pilot scaffolding

### Refactor

- Annotation outputs into claim-oriented outputs
- Ontology resolver into governed workflow service
- Review JSON flow into backend-ready governance models
- Commentary generation into schema-aligned composition

### Add

- Governed claim domain package
- Evidence/provenance package
- Governance/review service
- Commentary composition service
- Persistence layer for governed objects
- Minimal curator application surface

## Definition of Success

Phase 6 is successful when all of the following are true:

- Current ingestion outputs can be converted into governed candidate claims
- Ontology mappings no longer mutate canonical state without review
- Curator can approve or reject knowledge objects with evidence visibility
- Commentary can be generated from governed claims
- Reader retrieval can answer with approved commentary plus source anchoring

## Recommended Initial Corpus

Use two controlled tracks:

- Track A: 1 to 3 lectures
- Track B: 10 poems from one authoritative edition of `Diwan-e-Ghalib`

This keeps both ingestion modes in scope without exploding complexity.

## Risk Mitigation

### Risk 1: Governance Overhead Slows Ingestion

Mitigation: Automate candidate generation. Keep curator actions focused on approval, not creation.

### Risk 2: Ontology Fragmentation

Mitigation: Enforce canonical registry lookup before any new entity proposal. Require curator approval for all new entities.

### Risk 3: Storage Complexity Explosion

Mitigation: Use local filesystem for Phase 6. Introduce external stores only after governance models are proven.

### Risk 4: LLM Becomes De Facto Authority

Mitigation: Mark all AI outputs with provenance. Require human review before any claim enters canonical state.

### Risk 5: Multi-Language Complexity

Mitigation: Start with Urdu only. Design parsers as pluggable modules from day one.

## Next Phase

After Phase 6, the next phase should be:

`Phase 7: Scaled Knowledge Graph`

That phase should include:

- Full graph saturation for approved entities
- Large-scale reader application
- Multi-civilizational corpus expansion
- Advanced retrieval composition
- Collaborative scholar tooling
