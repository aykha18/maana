# Ma'na Implementation Roadmap: Architecture To System

## Purpose

This document translates Ma'na's architecture documents into an implementation sequence for the current repository.

It is the bridge between:

- first-principles architecture
- current ingestion code
- next product decisions

Its purpose is to answer:

- what remains valid in the current codebase
- what must be refactored
- what the MVP system boundaries should be
- what to build now versus later
- how to move from artifact ingestion to governed knowledge ingestion

## Inputs

This roadmap is derived from:

- [Architecture_Vision](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/Architecture_Vision)
- [ArchitectureVisionReadiness.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/ArchitectureVisionReadiness.md)
- [FirstPrinciplesOfMaana.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/FirstPrinciplesOfMaana.md)
- [CoreDomainModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/CoreDomainModel_v1.md)
- [InterpretationAndProvenanceModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/InterpretationAndProvenanceModel_v1.md)
- [OntologyAndCanonicalityModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/OntologyAndCanonicalityModel_v1.md)
- [CanonicalCommentarySchema_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/CanonicalCommentarySchema_v1.md)
- [EditorialWorkflowAndVersioning_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/EditorialWorkflowAndVersioning_v1.md)
- [RetrievalAndStorageArchitecture_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/RetrievalAndStorageArchitecture_v1.md)
- [IngestionPipelineTasks.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/IngestionPipelineTasks.md)

## Current System Reality

The current repository is strongest in one area:

- artifact ingestion for lectures

This includes:

- source download
- source preservation
- audio normalization
- segmentation
- transcription
- transcript cleaning
- structured annotation proposal generation

That is valuable and should be preserved.

However, the current system is not yet the Ma'na architecture.

It is a strong upstream ingestion pipeline that must now be connected to:

- governed claims
- ontology mapping
- canonical registry decisions
- curator workflow
- commentary artifacts
- hybrid storage and retrieval

## Implementation Principle

Do not throw away the current ingestion pipeline.

Do not pretend it is already the full architecture.

Instead:

- preserve what is already strong
- insert governance boundaries where meaning begins
- converge poem and lecture ingestion into shared knowledge objects
- delay full reader experience until knowledge governance is real

## What Remains Valid

The following current capabilities remain directly useful.

## 1. Source Preservation Pattern

The existing deterministic workspace and staged artifact preservation align strongly with the source preservation layer.

This should be retained.

## 2. Resumable Multi-Stage Processing

The current pipeline's stage-based structure is a good foundation for future governed processing.

## 3. Structured Intermediate Outputs

The current manifests, cleaned transcript outputs, and structured annotation outputs are the right habit.

These should evolve into governed claim-producing stages rather than be discarded.

## 4. Provider-Aware Annotation Layer

The specialized analyzer architecture is directionally correct.

It should be reframed as candidate claim generation rather than implicitly final knowledge.

## 5. File-Based Review Experiments

The poem dataset review and registry workflows are useful prototypes for curator governance.

They should not be mistaken for the final workflow, but they are a valid seed.

## What Must Be Refactored

The following areas require deliberate architectural transition.

## 1. Annotation Outputs Must Become Claim-Oriented

Current annotation results are still closer to extracted structured findings than governed claims.

They need to be normalized into:

- claim candidates
- evidence anchors
- provenance records
- mapping proposals

## 2. Ontology Resolution Must Stop Being An Endpoint Utility

The registry and resolver scaffolding exist, but ontology resolution must become part of a broader governed workflow, not a file-level append tool alone.

## 3. Commentary Must Become A First-Class Artifact

The current system does not yet produce canonical commentary documents structured according to the new schema.

## 4. Lecture And Poem Pipelines Must Converge

Right now there are two partially separate tracks:

- lecture artifact pipeline
- poem dataset pilot flow

These must converge into one shared governed knowledge model.

## 5. Storage Must Move Beyond Local Folder Semantics Alone

Local folders are still valuable for preserved source artifacts and generated files, but they are not sufficient for long-term governance, retrieval, and versioned curation.

## MVP System Boundary

The first real Ma'na architecture MVP should not try to deliver the entire long-term vision.

It should deliver the smallest honest system that reflects the architecture correctly.

## MVP Goal

Create a governed knowledge ingestion and curation loop for a small corpus with:

- preserved sources
- addressable units
- candidate claims
- ontology mapping proposals
- curator review
- commentary artifact generation
- reader-visible retrieval over approved knowledge

## Recommended Initial Corpus

Use two controlled tracks:

- Track A: 1 to 3 lectures
- Track B: 10 poems from one authoritative edition of `Diwan-e-Ghalib`

This keeps both ingestion modes in scope without exploding complexity.

## MVP Must Include

- source preservation
- governed unit identity
- claim candidate generation
- ontology registry lookup
- proposed versus approved mapping distinction
- curator review workflow
- commentary artifact generation for at least one supported scope
- reader retrieval for approved commentary and source evidence

## MVP Must Not Depend On

- full multi-civilizational scale
- full public reader application
- all commentary modes
- automatic canonical graph construction from all claims
- fully general OCR or manuscript pipelines
- all source types

## System Boundaries For The Current Repo

The implementation should now be split conceptually into the following bounded areas.

## 1. Ingestion Boundary

Responsible for turning raw sources into structured candidate artifacts.

### Includes

- download
- import
- transcription
- cleaning
- segmentation
- analyzer execution

### Must Output

- preserved source artifacts
- addressable units
- candidate claim bundles
- provenance-bearing intermediate artifacts

## 2. Knowledge Extraction Boundary

Responsible for converting cleaned transcript or poem text into candidate claims and draft commentary structures.

### Includes

- vocabulary extraction
- theme and human experience proposals
- symbolic and concept proposals
- commentary claim generation
- source anchoring

### Must Not Do

- silently canonicalize mappings
- silently finalize commentary

## 3. Governance Boundary

Responsible for:

- proposal queues
- review states
- ontology decisions
- version history
- approval scope
- reversibility

This is the true heart of Ma'na after ingestion.

## 4. Commentary Boundary

Responsible for composing governed commentary artifacts from approved or scoped claim sets.

## 5. Retrieval Boundary

Responsible for:

- source retrieval
- commentary retrieval
- ontology traversal
- graph traversal
- semantic retrieval

using governed stores rather than bypassing them.

## Datastore Responsibility Plan

The current repo should move toward a concrete hybrid responsibility split.

## 1. File Or Object Storage

Use for:

- original media
- downloaded sources
- OCR outputs
- imported texts
- transcripts
- derived document artifacts
- commentary files

### Near-Term Reality

The current local workspace already approximates this layer.

## 2. Structured Transactional Store

Use for:

- works
- witnesses
- units
- claims
- evidence
- provenance
- workflow states
- versions
- approvals

### Near-Term Recommendation

Start with one structured operational store before introducing full distributed complexity.

## 3. Ontology/Graph Store

Use for:

- ontology entities
- aliases
- semantic relations
- graph traversal edges
- merge and deprecation lineage

### Near-Term Recommendation

Keep graph scope small and governed first.

Do not attempt full graph saturation immediately.

## 4. Vector Store

Use for:

- embeddings
- retrieval chunks
- semantic recall

### Near-Term Recommendation

Only embed approved or explicitly scoped artifacts.

Do not embed raw experimental output as if it were stable knowledge.

## Ingestion-To-Governance Flow

The most important system bridge is the flow from artifacts to governed knowledge.

## Phase Flow

1. Preserve source
2. Produce addressable units
3. Generate candidate claims
4. Attach evidence and provenance
5. Propose ontology mappings
6. Place outputs in review queues
7. Curator approves, rejects, merges, splits, renames, or scopes
8. Compose commentary artifacts from governed claim sets
9. Publish approved artifacts for retrieval

## Rule

No step before governance may silently mutate the canonical layer.

## First Curator Workflow Scope

The first curator product should be smaller than a full editorial suite.

It should focus on the highest-value review actions only.

## Curator MVP Scope

- review proposed ontology mappings
- review proposed new ontology entities
- review unit-level commentary claim bundles
- approve or reject claim sets for limited scope
- inspect source evidence
- inspect provenance and AI involvement
- merge duplicate ontology proposals
- create or approve canonical mappings

## Curator MVP Must Show

- source snippet or evidence snippet
- addressed unit or work
- proposed ontology target
- evidence posture
- contributor and AI provenance
- current status
- prior related decisions

## Curator MVP Can Delay

- full visual graph editing
- large-scale bulk moderation
- advanced collaborative editorial discussion
- rich manuscript comparison tooling

## First Reader Retrieval Scope

The first reader experience should also be deliberately narrow.

It should prove the value of governed knowledge, not merely search over raw text.

## Reader MVP Scope

- ask a question
- retrieve approved commentary
- retrieve supporting source passage
- retrieve linked ontology entities
- retrieve related works or units through governed relations

## Reader MVP Must Show

- explanation
- source anchoring
- uncertainty or contested status where relevant
- related concepts and human experiences
- path to original source material

## Reader MVP Must Avoid

- pretending unresolved material is final truth
- flattening all traditions into one answer
- hiding whether the answer is sourced, interpreted, or synthesized

## Recommended Build Sequence

The current repository should now move through the following implementation sequence.

## Step 1. Stabilize Artifact Ingestion As Upstream Infrastructure

Keep the existing lecture ingestion pipeline working.

Do not keep expanding it blindly.

Focus on making it a reliable upstream source-preservation and candidate-generation engine.

## Step 2. Introduce Governed Claim Models

Add first-class models for:

- claim candidate
- evidence anchor
- provenance record
- review state
- approval scope

This is the most important code transition.

## Step 3. Convert Annotation And Poem Resolution Outputs Into Claim Bundles

Refactor current outputs so lecture and poem pipelines emit the same governed intermediate shape.

## Step 4. Build Curator Backend First

Before a full UI, create the backend structures for:

- review queue items
- decisions
- version history
- ontology proposal lifecycle
- commentary approval lifecycle

## Step 5. Build Curator UI For Review-Critical Actions

Implement the smallest useful curator workflow around:

- ontology proposals
- claim approval
- evidence inspection
- commentary promotion

## Step 6. Generate Canonical Commentary Artifacts

Create commentary composition from governed claim sets using the new schema.

## Step 7. Build Reader Retrieval Over Approved Knowledge

Only after the approval path exists should the first reader retrieval surface be built.

## Step 8. Add Hybrid Persistence Beyond Local Files

Introduce the structured operational store, then vector and graph layers in limited governed scope.

## Build Now Versus Later

## Build Now

- claim-oriented intermediate models
- governance state models
- ontology proposal queues
- evidence anchoring
- provenance capture
- curator backend
- narrow curator UI
- commentary composition for one or two scopes
- reader retrieval over approved commentary and source

## Build Later

- broad public reader application
- large-scale graph exploration
- generalized multi-source ingestion beyond controlled pilots
- collaborative scholar tooling
- advanced multilingual reasoning
- full manuscript ecosystem

## Codebase Implications

For the current `maana-ingest` codebase, this means:

## Keep

- downloader
- workspace layout discipline
- audio preparation
- transcription
- cleaning
- annotation analyzers
- readiness checks
- poem pilot scaffolding

## Refactor

- annotation outputs into claim-oriented outputs
- ontology resolver into governed workflow service
- review JSON flow into backend-ready governance models
- commentary generation into schema-aligned composition

## Add

- governed claim domain package
- evidence/provenance package
- governance/review service
- commentary composition service
- persistence layer for governed objects
- minimal curator application surface

## Suggested Near-Term Milestones

## Milestone 1. Architecture-Conformant Phase 6 Foundation

Deliver:

- governed claim models
- provenance/evidence models
- lecture and poem candidate claim emission

## Milestone 2. Curator Backend MVP

Deliver:

- review queues
- ontology proposal lifecycle
- scoped approvals
- version history

## Milestone 3. Curator UI MVP

Deliver:

- review screen for ontology mappings and commentary claims
- evidence inspection
- approval actions

## Milestone 4. Commentary Composition MVP

Deliver:

- unit commentary artifact
- work commentary artifact
- provenance-aware render

## Milestone 5. Reader Retrieval MVP

Deliver:

- question to approved commentary
- linked source evidence
- related ontology navigation

## Definition Of Success For The Next Real Phase

The next real phase is successful when all of the following are true:

- current ingestion outputs can be converted into governed candidate claims
- ontology mappings no longer mutate canonical state without review
- curator can approve or reject knowledge objects with evidence visibility
- commentary can be generated from governed claims
- reader retrieval can answer with approved commentary plus source anchoring

## Final Recommendation

Do not continue Phase 6 as a narrow extractor-only phase.

Instead, reinterpret the next implementation phase as:

`Phase 6: Governed Knowledge Layer`

That phase should include:

- claim models
- evidence and provenance
- ontology proposal workflow
- curator backend
- first commentary composition path

Only after that should Ma'na scale outward into full reader and graph experiences.
