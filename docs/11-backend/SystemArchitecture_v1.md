# Ma'na System Architecture v1

## Purpose

This document defines the concrete system architecture for Ma'na Phase 6 and Phase 0.

It translates the architecture vision, domain model, and implementation plan into:

- Service boundaries
- Data flow
- API contracts
- Storage responsibilities
- Deployment topology

This document is implementation-facing. It must not redefine ontology concepts.

## Architecture Principles

1. **Knowledge before interface** — Technology serves the intellectual model.
2. **Separation of concerns** — Each service has one job.
3. **Governance first** — No knowledge enters the canonical layer without review.
4. **Reversibility** — Every action can be undone.
5. **Addressability** — Every entity has a stable identifier.
6. **Provenance everywhere** — Every claim carries its history.
7. **AI as contributor, not authority** — AI outputs are proposals, not facts.
8. **Semantic graph is the source of truth** — World numbers are identifiers, not semantic positions.
9. **Three-layer truth** — PostgreSQL = canonical truth, Neo4j = relationships, Vector = semantic proximity.

## System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Curator App  │  │ Reader App   │  │ Ingestion CLI        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                                │
│              (Authentication, Rate Limiting)                     │
└─────────┬─────────────────┬─────────────────────┬──────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────┐ ┌─────────────────┐ ┌───────────────────────┐
│ Curator Service │ │ Reader Service  │ │ Ingestion Service     │
│                 │ │                 │ │                       │
│ /review/*       │ │ /query/*        │ │ /ingest/*             │
│ /governance/*   │ │ /retrieve/*     │ │ /pipeline/*           │
└────────┬────────┘ └────────┬────────┘ └──────────┬────────────┘
         │                   │                      │
         ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Claim Service│  │Ontology Svc  │  │ Commentary Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Review Svc    │  │Retrieval Svc │  │ Provenance Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Semantic Svc  │  │Projection Svc│  │ Agent Orchestrator    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────┬─────────────────┬─────────────────────┬──────────────┘
          │                 │                     │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ PostgreSQL   │  │   Neo4j      │  │      Qdrant          │  │
│  │ (Governed)   │  │ (Ontology)   │  │  (Semantic)          │  │
│  │ + pgvector   │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐                                              │
│  │ MinIO/S3     │                                              │
│  │ (Sources)    │                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Services

### 1. Ingestion Service

Responsible for turning raw sources into structured candidate artifacts.

Endpoints:

- `POST /ingest/url` — Ingest from URL
- `POST /ingest/file` — Ingest from file upload
- `GET /ingest/{job_id}/status` — Get ingestion status
- `GET /ingest/{job_id}/artifacts` — Get preserved artifacts

Responsibilities:

- Download and preserve source
- Audio normalization and segmentation
- Transcription
- Transcript cleaning
- Candidate claim generation
- Vocabulary extraction
- Structured intermediate output

Does not:

- Mutate canonical state
- Finalize commentary
- Make ontology decisions

### 2. Claim Service

Responsible for managing the lifecycle of claims.

Endpoints:

- `POST /claims` — Create claim candidate
- `GET /claims/{id}` — Get claim with evidence and provenance
- `PUT /claims/{id}` — Update claim (draft only)
- `POST /claims/{id}/evidence` — Attach evidence
- `POST /claims/{id}/provenance` — Attach provenance
- `GET /claims?unit_id={id}` — Get claims for unit
- `GET /claims?status={status}` — Get claims by status

Responsibilities:

- Claim CRUD
- Evidence attachment
- Provenance capture
- Status transitions (draft → proposed → approved → rejected → deprecated)

### 3. Ontology Service

Responsible for managing ontology entities and mappings.

Endpoints:

- `POST /ontology/propose` — Propose new entity or mapping
- `GET /ontology/search?q={query}` — Search canonical registry
- `POST /ontology/{id}/approve` — Approve proposal
- `POST /ontology/{id}/reject` — Reject proposal
- `POST /ontology/{id}/merge` — Merge with existing
- `GET /ontology/entities` — List entities
- `GET /ontology/entities/{id}/relations` — Get relations

Responsibilities:

- Canonical registry management
- Proposal lifecycle
- Alias and merge lineage
- Relation management

Does not:

- Mutate canonical entities without approval
- Silently create duplicates

### 4. Review Service

Responsible for curator review workflows.

Endpoints:

- `GET /review/queue` — Get review queue
- `POST /review/{item_id}/approve` — Approve item
- `POST /review/{item_id}/reject` — Reject item
- `POST /review/{item_id}/merge` — Merge item
- `POST /review/{item_id}/split` — Split item
- `POST /review/{item_id}/rename` — Rename item
- `GET /review/decisions` — Get decision history

Responsibilities:

- Queue management
- Approval workflows
- Version history
- Decision audit trail

### 5. Commentary Service

Responsible for composing commentary from governed claims.

Endpoints:

- `POST /commentary/compose` — Compose commentary from claim set
- `GET /commentary/{id}` — Get commentary
- `GET /commentary/{id}/claims` — Get underlying claims
- `GET /commentary/{id}/provenance` — Get provenance
- `PUT /commentary/{id}` — Update commentary draft
- `POST /commentary/{id}/publish` — Publish commentary

Responsibilities:

- Commentary composition
- Version management
- Claim linkage
- Provenance preservation

### 6. Retrieval Service

Responsible for layered retrieval across all knowledge types.

Endpoints:

- `POST /retrieve/source` — Source retrieval
- `POST /retrieve/commentary` — Commentary retrieval
- `POST /retrieve/claims` — Claim retrieval
- `POST /retrieve/ontology` — Ontology retrieval
- `POST /retrieve/graph` — Graph traversal
- `POST /retrieve/semantic` — Semantic retrieval
- `POST /retrieve/compose` — Composed multi-layer retrieval

Responsibilities:

- Query routing
- Result composition
- Source anchoring
- Uncertainty representation

### 7. Semantic Service

Responsible for managing Worlds, Chapters, Parts, SemanticClusters, WordFamilies, and semantic paths.

Endpoints:

- `POST /worlds` — Create World
- `GET /worlds/{id}` — Get World
- `GET /worlds/{id}/related` — Get related Worlds
- `GET /worlds/{id}/path` — Get semantic paths
- `GET /worlds/{id}/graph` — Get graph neighborhood
- `GET /chapters/{id}` — Get Chapter
- `GET /chapters/{id}/architecture` — Get chapter architecture analysis
- `POST /semantic/analyze` — Run semantic analysis
- `POST /semantic/propose-relations` — Propose relations
- `POST /semantic/review` — Review semantic proposals
- `GET /gaps` — Get detected semantic gaps
- `GET /architecture/proposals` — Get architecture proposals
- `GET /architecture/history` — Get architecture history
- `POST /worlds/{id}/architect` — Run architect agent on World

Responsibilities:

- World CRUD
- Chapter and cluster management
- Semantic path management
- Agent proposal ingestion
- Architecture snapshot management

Does not:

- Mutate canonical graph without human approval
- Silently restructure chapters

### 8. Semantic Projection Service

Responsible for keeping PostgreSQL, Neo4j, and Qdrant in sync.

Responsibilities:

- Listen for WORLD_CREATED, WORLD_UPDATED, WORLD_RELATION_CHANGED, WORLD_DELETED events
- Regenerate embeddings for changed Worlds
- Update Neo4j graph for changed Worlds
- Update vector index for changed Worlds

### 9. Agent Orchestrator

Responsible for running the semantic engine agents.

Agents:

- **Ingestion Agent** — Parse new World proposals, extract definitions, themes, word families
- **Relation Agent** — Discover relations between Worlds using vector retrieval + LLM reasoning
- **Architect Agent** — Propose chapter placement, cluster membership, architectural changes
- **Ring Agent** — Evaluate chapter semantic topology and coherence
- **Gap Agent** — Detect missing Worlds from graph holes, vector clusters, and literary corpus
- **Quality Agent** — Validate provenance, distinguish content types, enforce quality rules

Responsibilities:

- Agent execution
- Proposal generation
- Confidence scoring
- Audit logging

## Data Models

### Core Domain Objects

```
Source
Work
Witness
Segment
Unit
Claim
Evidence
ProvenanceRecord
Contributor
Tradition
OntologyEntity
Relationship
Question
CommentaryDocument
World
Chapter
Part
SemanticCluster
WordFamily
Relation
SemanticPath
ArchitectureSnapshot
```

### Claim States

```
draft
proposed
reviewed
approved
disputed
rejected
deprecated
```

### Evidence Types

```
textual_span
lexical
manuscript
historical
scholarly_commentary
comparative_passage
interpretive_tradition
```

### Claim Types

```
factual
descriptive
interpretive
comparative
historical
ontological
relational
editorial
inferential
```

### Provenance Contributor Types

```
human_editor
scholar
curator
translator
reader
ai_system
ingestion_pipeline
```

## Storage Architecture

### PostgreSQL (Structured Governance Layer)

Tables:

- `works` — Work metadata
- `witnesses` — Witness metadata
- `segments` — Segment definitions
- `units` — Unit definitions
- `claims` — Claim records
- `evidence` — Evidence records
- `provenance_records` — Provenance records
- `contributors` — Contributor registry
- `traditions` — Tradition registry
- `review_items` — Review queue items
- `decisions` — Decision history
- `commentaries` — Commentary metadata
- `versions` — Version history

Semantic layer tables:

- `worlds` — World definitions with multilingual terms and semantic properties
- `chapters` — Chapter definitions
- `parts` — Part definitions
- `clusters` — SemanticCluster definitions
- `word_families` — WordFamily definitions
- `relations` — Relation definitions
- `poets` — Poet registry
- `themes` — Theme registry
- `symbols` — Symbol registry
- `sources` — Source registry
- `citations` — Citation records
- `world_versions` — World version history
- `embeddings` — Multiple typed embeddings per World
- `semantic_analysis` — Semantic analysis results
- `architecture_snapshots` — Architecture version snapshots
- `agent_runs` — Agent execution logs
- `agent_proposals` — Agent proposals awaiting review

pgvector extensions:

- `embedding_full`
- `embedding_definition`
- `embedding_meaning`
- `embedding_literary`
- `embedding_philosophical`
- `embedding_modern`
- `embedding_questions`

Indexes:

- `claims.unit_id` — Fast claim lookup by unit
- `claims.status` — Fast status filtering
- `evidence.claim_id` — Fast evidence lookup
- `review_items.status` — Fast queue filtering
- `worlds.chapter_id` — Fast chapter lookup
- `worlds.cluster_id` — Fast cluster lookup
- `relations.source_world_id` — Fast relation traversal
- `relations.target_world_id` — Fast relation traversal
- `embeddings.world_id` — Fast embedding lookup

### Neo4j (Ontology Layer)

Nodes:

- `OntologyEntity` — themes, symbols, concepts, human experiences, questions
- `World` — semantic concepts
- `Chapter` — semantic chapters
- `SemanticCluster` — semantic clusters
- `Unit` — addressable units
- `Contributor` — contributors

Edges:

- `EVOKES` — Unit → OntologyEntity
- `MAPS_TO` — Claim → OntologyEntity
- `RELATES_TO` — OntologyEntity → OntologyEntity
- `BELONGS_TO` — Work → Collection
- `WROTE` — Author → Work
- `CONTAINS` — Witness → Segment
- `PART_OF` — World → Chapter / Chapter → Part / Cluster → Part
- `PRECEDES` — World → World
- `FOLLOWS` — World → World
- `DEEPENS` — World → World
- `EXPANDS` — World → World
- `RELATED_TO` — World → World
- `CONTRASTS_WITH` — World → World
- `OPPOSITE_OF` — World → World
- `WORD_FAMILY` — World → World
- `DERIVED_FROM` — World → World
- `SYNONYM_OF` — World → World
- `USED_BY` — World → Poet
- `THEME_OF` — World → Theme
- `SYMBOLIZED_BY` — World → Symbol
- `RING_LINK` — World → World (chapter ring)
- `CHAPTER_ANCHOR` — World → Chapter
- `CLUSTER_ANCHOR` — World → SemanticCluster
- `TRANSITION_TO` — World → World

### Qdrant (Semantic Retrieval Layer)

Collections:

- `source_segments` — Embeddings for source segments
- `approved_commentary` — Embeddings for approved commentary sections
- `claim_bundles` — Embeddings for governed claim bundles
- `ontology_descriptions` — Embeddings for ontology entity descriptions
- `world_full` — Full World embeddings
- `world_definition` — World definition embeddings
- `world_meaning` — World meaning embeddings
- `world_literary` — World literary embeddings
- `world_philosophical` — World philosophical embeddings
- `world_modern` — World modern interpretation embeddings
- `world_questions` — World question embeddings

Rule: Only approved or explicitly scoped artifacts are embedded.

### MinIO (Source Preservation Layer)

Buckets:

- `raw-sources` — Original uploaded/downloaded files
- `transcripts` — Generated transcripts
- `derivatives` — Audio/video derivatives
- `commentary-sources` — Imported commentary texts
- `generated-commentary` — Composed commentary artifacts

## API Design Principles

1. **RESTful** — Resources are addressed by stable identifiers
2. **Versioned** — All APIs are versioned from day one
3. **Provenance-aware** — All mutations include provenance metadata
4. **Status-explicit** — All knowledge objects have explicit status
5. **Addressable** — Every entity is retrievable by ID
6. **Auditable** — All mutations produce immutable audit records
7. **Semantic-type aware** — The semantic graph preserves relationship type

## Authentication and Authorization

### Authentication

- JWT tokens for human curators and readers
- API keys for service-to-service communication
- OAuth2 for external contributors (future)

### Authorization

- Curators: full write access to review queues, limited write to ontology
- Readers: read-only access to approved knowledge
- Ingestion pipeline: write access to draft/proposed state only
- AI services: propose access only, no direct canonical writes

## Deployment Topology

### Phase 6.1-6.2 (Development)

- Single Docker Compose deployment
- PostgreSQL, Neo4j, Qdrant, MinIO all local
- Ingestion service and API in same process
- No external load balancer

### Phase 6.3+ (Staging)

- Separate containers for each service
- PostgreSQL with persistence volume
- Neo4j with persistence volume
- Qdrant with persistence volume
- MinIO with persistence volume
- API Gateway (Caddy or Traefik)
- Separate ingestion worker process

### Phase 7+ (Production)

- Kubernetes or similar orchestration
- Managed databases (or high-availability self-hosted)
- CDN for source artifacts
- Separate reader and curator deployment tiers
- Monitoring and observability stack

## Observability

### Logging

- Structured JSON logs for all services
- Correlation IDs for request tracing
- Provenance events logged separately from system events

### Metrics

- Ingestion pipeline stage duration
- Claim proposal rate
- Approval/rejection rate
- Review queue depth
- Retrieval latency by layer
- Embedding generation rate
- Agent execution duration
- Agent proposal acceptance rate
- Semantic projection sync latency
- Ring score changes over time

### Tracing

- Distributed tracing across services
- Claim lifecycle tracing (proposed → approved → published)

## Development Workflow

### Branching Strategy

- `main` — stable, deployable
- `develop` — integration branch
- `feature/*` — feature branches
- `milestone/*` — milestone branches

### Code Review

- All changes require review
- Architecture changes require ADR
- Ontology changes require curator approval

### Testing Strategy

- Unit tests for domain models
- Integration tests for service boundaries
- Pipeline tests for ingestion stages
- Contract tests for API boundaries
- Mock LLM for reproducible tests

## Migration Strategy

### From Current State

1. Keep existing ingestion pipeline functional
2. Add governed claim models alongside existing outputs
3. Introduce governance service as new module
4. Converge lecture and poem pipelines into shared models
5. Migrate storage incrementally

### Backward Compatibility

- Existing local workspace artifacts remain valid
- Existing manifests are preserved
- New governed outputs are additive, not replacement

## Technology Constraints

- Python 3.12+ for backend services
- FastAPI for API services
- Pydantic for validation
- SQLModel/SQLAlchemy for PostgreSQL access
- Neo4j Python driver for graph access
- Qdrant client for vector access
- MinIO client for object storage
- Docker for containerization
- No frontend framework prescribed yet

## Non-Negotiables

1. Every claim must have evidence and provenance
2. No canonical mutation without governance
3. Source artifacts are never discarded
4. AI outputs are always marked
5. Uncertainty is representable
6. Disagreement is preservable
7. Multiplicity survives normalization
8. PostgreSQL is the source of truth for canonical objects
9. Neo4j is the source of truth for semantic relationships
10. Vector index is for semantic proximity only, not truth
11. No AI agent may silently mutate canonical architecture
12. Every structural change must be explainable, versioned, and reversible
13. World numbers are identifiers, not semantic positions
