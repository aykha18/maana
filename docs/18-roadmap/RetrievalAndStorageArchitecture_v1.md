# Ma'na Retrieval And Storage Architecture v1

## Purpose

This document defines how Ma'na's knowledge model should be represented for storage, retrieval, reasoning, and preservation.

It does not prescribe a single database product or deployment topology.

Its purpose is to explain:

- why Ma'na requires hybrid storage
- what kinds of knowledge belong in which storage layer
- how retrieval should operate without collapsing source, claim, ontology, commentary, and AI synthesis into one substrate
- how preservation and reasoning should coexist

This document derives from:

- [CoreDomainModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/CoreDomainModel_v1.md)
- [InterpretationAndProvenanceModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/InterpretationAndProvenanceModel_v1.md)
- [OntologyAndCanonicalityModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/OntologyAndCanonicalityModel_v1.md)
- [CanonicalCommentarySchema_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/CanonicalCommentarySchema_v1.md)
- [EditorialWorkflowAndVersioning_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/EditorialWorkflowAndVersioning_v1.md)

## Foundational Principle

No single storage model is sufficient for Ma'na.

Ma'na is simultaneously:

- a preservation system
- a governed knowledge system
- a commentary corpus
- a semantic retrieval system
- a knowledge graph
- an AI reasoning substrate

If these are forced into one storage paradigm, critical distinctions will be lost.

Therefore Ma'na should be designed as a hybrid architecture with clear layer boundaries.

## Why Hybrid Storage Is Necessary

Different kinds of objects have fundamentally different needs.

### Source Artifacts Need

- preservation
- immutability
- version-aware retention
- large binary support

### Governed Knowledge Objects Need

- identity
- referential integrity
- auditability
- versioning
- scoped status

### Ontology And Relations Need

- graph traversal
- stable identifiers
- merge and alias handling
- reusable semantic connections

### Commentary Needs

- structured human-readable documents
- embedded references
- revision history
- retrieval-friendly segmentation

### AI Retrieval Needs

- embedding search
- chunk or unit retrieval
- semantic similarity
- question-conditioned recall

These needs are related, but not identical.

## Storage Layers

Ma'na should be modeled as at least five conceptual storage layers.

## 1. Source Preservation Layer

This layer stores original and derived source artifacts.

### Examples

- manuscript images
- PDFs
- audio
- video
- OCR output
- transcripts
- translations
- imported commentary texts

### Properties

- append-preserving
- non-destructive
- provenance-carrying
- addressable

### Purpose

This layer protects the evidence base.

It is the outer archive of Ma'na.

### Best Fit

Object storage or durable document preservation storage.

## 2. Structured Governance Layer

This layer stores governed objects whose lifecycle, identity, and review state matter.

### Examples

- works
- witnesses
- segments
- units
- claims
- evidence records
- provenance records
- commentary identities
- editorial states
- version history

### Properties

- stable identifiers
- referential integrity
- transactional updates where needed
- explicit version lineage
- auditability

### Purpose

This is the operational backbone of governed knowledge.

### Best Fit

Relational or strongly structured persistence.

## 3. Ontology And Relation Layer

This layer stores reusable semantic entities and governed relations.

### Examples

- themes
- symbols
- concepts
- human experiences
- literary devices
- traditions
- ontology aliases
- merge lineage
- semantic relations

### Properties

- stable node identity
- relation traversal
- merge/split lineage
- scoped relation assertions

### Purpose

This layer supports semantic connectivity across the corpus.

### Best Fit

Graph-oriented storage, or a graph-capable relation layer built on top of a structured core.

## 4. Commentary Document Layer

This layer stores the composed human-readable knowledge artifacts used for explanation, teaching, comparison, and reader experience.

### Examples

- unit commentary documents
- work commentary documents
- question-centered commentary
- tradition-specific commentary

### Properties

- rich structured text
- internal references
- section-aware segmentation
- revision traceability
- embedding-friendly shape

### Purpose

This layer is the readable reasoning corpus.

### Best Fit

Document-oriented storage with durable identifiers and version linkage.

## 5. Semantic Retrieval Layer

This layer stores representations used for embedding search and retrieval-time AI assistance.

### Examples

- embeddings
- retrieval chunks
- semantic summaries
- vector indexes
- retrieval hints

### Properties

- regenerable
- query-optimized
- derivable from governed or approved artifacts
- non-authoritative

### Purpose

This layer accelerates discovery and AI-assisted reasoning, but must not become the source of truth.

### Best Fit

Vector search infrastructure and derivative retrieval stores.

## Separation Of Responsibilities

These layers must collaborate, but not collapse into one another.

## Source Preservation Layer Must Not

- silently store interpretations as source truth
- lose original artifacts after transformation
- overwrite witness variation

## Structured Governance Layer Must Not

- replace readable commentary documents
- become the sole reader-facing explanation layer
- absorb every binary or large source artifact

## Ontology Layer Must Not

- become a freeform tag bucket
- absorb commentary
- store unstable interpretations as canonical entities

## Commentary Layer Must Not

- become the sole place where truth, scope, evidence, and provenance are hidden
- overwrite structured governance records

## Semantic Retrieval Layer Must Not

- be treated as canonical memory
- outrank governed evidence and provenance
- silently synthesize away disagreement

## Canonical Versus Derived Storage

One of the most important architectural boundaries is between canonical stores and derived stores.

## Canonical Or Governed Stores

These contain objects whose identity and review history matter.

### Examples

- source artifact metadata
- works
- witnesses
- units
- claims
- evidence
- provenance
- ontology entities
- mappings
- commentary identities
- approval history

## Derived Stores

These contain useful but regenerable representations.

### Examples

- embeddings
- retrieval chunks
- semantic summaries
- ranking features
- recommendation caches
- graph projections

### Rule

Derived stores may be deleted and regenerated.

Canonical stores may not be treated that way.

## Retrieval Architecture Principles

Retrieval in Ma'na should not be a single search function.

It should be a layered retrieval architecture that respects knowledge type.

## 1. Source Retrieval

Used when the user or system needs original evidence.

### Examples

- show the source passage
- locate the witness
- inspect the original wording

## 2. Commentary Retrieval

Used when the system needs explanatory artifacts.

### Examples

- retrieve unit commentary on longing
- retrieve question-centered commentary on exile

## 3. Claim Retrieval

Used when the system needs governed knowledge objects rather than only prose documents.

### Examples

- retrieve approved claims about this symbol
- retrieve contested interpretations of this passage

## 4. Ontology Retrieval

Used when the system needs reusable semantic anchors.

### Examples

- find all works linked to `longing`
- find all uses of the symbol `wine`

## 5. Graph Retrieval

Used when the system needs traversable relations.

### Examples

- move from `hope` to `waiting` to `suffering`
- move from a question to related concepts and commentary

## 6. Semantic Retrieval

Used when exact structure is not enough and similarity or conceptual resonance matters.

### Examples

- find passages semantically similar to this feeling
- retrieve commentary relevant to loneliness after success

## Retrieval Composition Principle

Strong Ma'na retrieval should often combine layers, not rely on one.

### Example Flow

1. semantic retrieval finds candidate units and commentary
2. ontology retrieval finds linked concepts and experiences
3. graph retrieval expands connected nodes
4. claim retrieval finds approved and contested interpretations
5. source retrieval verifies evidence

This is closer to reasoning than ordinary document search.

## Query Modes

Ma'na should support distinct query modes because different user intents require different retrieval pathways.

## 1. Source-Seeking Query

The user wants original text, source evidence, or witness comparison.

## 2. Explanation-Seeking Query

The user wants commentary and guided understanding.

## 3. Concept-Seeking Query

The user wants ontology-level exploration.

## 4. Question-Seeking Query

The user wants the system to engage a human question across works.

## 5. Disagreement-Seeking Query

The user wants competing interpretations, not one flattened answer.

## 6. Comparative Query

The user wants relationships across authors, traditions, or civilizations.

Retrieval should not force all these modes through one index.

## Embeddings And Vector Storage

Embeddings are important, but they must remain subordinate to governed knowledge.

## Appropriate Embedding Targets

Embeddings should primarily be built from:

- source segments
- approved commentary sections
- governed claim bundles
- question-centered commentary
- ontology descriptions

## Embedding Boundaries

Embeddings should not be treated as:

- canonical memory
- sufficient provenance
- evidence by themselves
- replacements for graph relations

## Recommended Principle

Vector search should propose candidates.

Governed layers should determine what those candidates mean.

## Graph Architecture Principles

The graph should not be built from loose co-occurrence alone.

It should be built from governed relations and reusable ontology connections.

## Good Graph Inputs

- approved ontology mappings
- curated cross-reference relations
- supported claim-to-claim relations
- stable work-to-author and work-to-collection relations
- governed question-to-concept links

## Weak Graph Inputs

- raw keyword overlap
- unreviewed AI similarity labels
- temporary commentary phrasing

### Rule

Weak inputs may inform candidate generation, but should not directly become graph core structure.

## Commentary Storage Principles

Commentary should exist both as:

- readable artifact
- structured composition

This means commentary storage should preserve:

- document-level coherence
- section structure
- linked claims
- linked ontology references
- linked source anchors
- version lineage

A system that stores commentary only as freeform markdown will lose governance power.

A system that stores commentary only as structured records will lose readability and pedagogical richness.

Ma'na therefore needs both.

## Source Preservation Principles

Ma'na must retain:

- original source
- parsed source
- transformed source
- extracted units
- imported commentary sources
- generated derivatives

Nothing important should disappear after processing.

This is especially critical for:

- OCR pipelines
- speech transcription
- translated witnesses
- AI-assisted transformations

## Identity And Addressability Requirements

Every layer must preserve compatible identifiers so that retrieval can move across layers without ambiguity.

At minimum, the architecture should support addressability for:

- source artifact
- witness
- segment
- unit
- claim
- commentary artifact
- ontology entity
- relation
- question
- version

Without addressability, there can be no governed retrieval.

## Storage By Knowledge Object

The following conceptual placement is recommended.

## Source Artifacts

- primary home: source preservation layer
- secondary metadata presence: governance layer

## Works, Witnesses, Units

- primary home: governance layer
- graph exposure where relationally useful

## Claims, Evidence, Provenance

- primary home: governance layer
- graph exposure for relation traversal where appropriate

## Ontology Entities And Stable Relations

- primary home: ontology and relation layer
- indexed in governance layer for registry and review history if needed

## Commentary Artifacts

- primary home: commentary document layer
- linked structurally to governance layer
- embedded in retrieval layer

## Embeddings And Retrieval Chunks

- primary home: semantic retrieval layer
- always linked back to governed source identities

## Audit And Version History

Version and audit history should not be treated as optional appendices.

They are part of the retrieval architecture too.

Ma'na should support retrieval such as:

- show current approved commentary
- show prior version
- show why it changed
- show what ontology mapping was deprecated
- show AI-influenced revisions

This means storage must preserve history as first-class navigable knowledge.

## Reader Retrieval Versus Curator Retrieval

Reader and curator experiences should not query the system in the same way.

## Reader Retrieval Priorities

- clarity
- explanation
- trustworthy synthesis
- source anchoring
- humane navigation

## Curator Retrieval Priorities

- provenance
- audit trail
- conflicts
- pending proposals
- duplicate detection
- version diffs
- contested mappings

The same underlying data may serve both, but the retrieval pathways should differ.

## Cross-Lingual Retrieval

Because Ma'na spans civilizations and languages, retrieval must distinguish:

- source language
- commentary language
- ontology identity
- translated expression

The architecture should allow a user to retrieve by meaning without losing the original linguistic grounding.

This is one of the strongest arguments for keeping ontology, commentary, and source layers separate but linked.

## Failure Modes To Avoid

Any future implementation violates this architecture if it:

- stores all knowledge only as documents
- stores all knowledge only as rows and loses commentary richness
- stores all knowledge only in vectors
- lets vector similarity override evidence and provenance
- treats graph edges as ungoverned co-occurrence
- discards source artifacts after extraction
- stores commentary with no linkage to claims or sources
- stores ontology without relation to governance history

## Recommended Technology Pattern

Without prescribing exact vendors, the architecture naturally points toward a hybrid stack:

- object storage for preserved source artifacts and large derivatives
- structured transactional storage for governed entities and workflow states
- graph-oriented storage for reusable semantic relations
- document-oriented storage for commentary artifacts
- vector infrastructure for semantic retrieval

This is not complexity for its own sake.

It is a direct consequence of the knowledge model.

## Practical Consequence For Current Ma'na

The current ingestion pipeline already aligns partially with this direction because it preserves staged artifacts.

However, the future architecture must evolve so that:

- lecture and poem ingestion converge into governed knowledge objects
- commentary becomes structurally linked rather than stored as standalone prose
- ontology mappings become governed claims
- retrieval can combine semantic search, graph traversal, and source verification

## Next Best Step

The conceptual architecture stack is now strong enough that the next step should not be more abstract design alone.

The strongest next step is to create an implementation bridge document such as:

- `ImplementationRoadmap_ArchitectureToSystem.md`

That document should translate the architecture set into:

- MVP system boundaries
- datastore responsibilities
- ingestion-to-governance flow
- first curator workflow scope
- first reader retrieval scope
- what to build now versus later
