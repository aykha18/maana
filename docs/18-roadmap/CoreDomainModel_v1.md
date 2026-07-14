# Ma'na Core Domain Model v1

## Purpose

This document translates the constitutional principles of Ma'na into a stable domain model.

It is not a database schema, API contract, or implementation plan.

Its purpose is to define the core entities, relationships, invariants, and governance boundaries that every future schema, workflow, storage model, and AI system must preserve.

This document should remain valid across:

- poetry
- scripture
- philosophy
- plays
- novels
- essays
- letters
- speeches
- oral traditions

It should also remain valid across languages, civilizations, and evolving scholarly traditions.

## Domain Model Principles

### 1. Source Precedes Interpretation

Every meaning-bearing structure in Ma'na begins with source material.

Interpretation, ontology mapping, graph relationships, and AI synthesis are downstream layers.

### 2. Addressability Is Essential

Knowledge cannot be governed unless it can be addressed precisely.

Ma'na therefore requires a way to refer not only to works, but also to editions, spans, units, claims, ontology entities, and interpretations.

### 3. Claims Are The Core Knowledge Entity

The central active entity in Ma'na is the anchored claim:

> a claim with scope, evidence, provenance, and status

Everything else either grounds claims, organizes claims, or is derived from claims.

### 4. Canonicality Is A Governance Layer

Canonicality does not define what exists.

It defines what is stable enough to be reused, linked, approved, and operationalized across the system.

### 5. Multiplicity Must Survive Normalization

Normalization should reduce duplication, not erase disagreement.

The domain model must preserve plurality even when it introduces stable reference entities.

## Primary Entities

## 1. Source

### Definition

A source is any preserved input artifact from which Ma'na derives knowledge.

### Examples

- manuscript
- printed edition
- lecture audio
- transcription
- translation
- commentary book
- scholarly article
- oral recitation
- user-submitted note

### Role

Source is the outer boundary of evidence preservation.

Ma'na never discards the source layer.

## 2. Work

### Definition

A work is an identifiable cultural or intellectual artifact treated as a coherent object of study.

### Examples

- a ghazal
- a play
- a novel
- a sermon
- a philosophical dialogue
- a sacred text
- a speech

### Important Clarification

Work is not limited to poem.

Poem is only one subtype or manifestation of Work.

## 3. Witness

### Definition

A witness is a specific textual or transmitted instance of a work.

### Examples

- edition
- manuscript witness
- recited version
- translated version
- edited publication

### Role

Witness allows Ma'na to preserve textual variation without forcing all versions into one canonical text.

## 4. Segment

### Definition

A segment is any addressable span inside a witness or source.

### Examples

- couplet
- line
- stanza
- paragraph
- scene
- chapter
- ayah
- hadith passage
- section
- utterance

### Role

Segment is the general answer to the question of addressability.

It avoids overcommitting to verse-only or prose-only assumptions.

## 5. Unit

### Definition

A unit is a segment that has been editorially recognized as a meaning-bearing interpretive boundary.

### Difference From Segment

All units are segments.

Not all segments are units.

This distinction matters because addressable spans may be mechanically segmented, while units reflect editorial or tradition-aware judgment.

### Role

Unit is the main attachment point for commentary, interpretation, and ontology mapping.

## 6. Claim

### Definition

A claim is the smallest active knowledge object in Ma'na.

It asserts something about a source, work, witness, unit, ontology entity, relation, or interpretation.

### Claim Types

At minimum, claims may be:

- factual
- descriptive
- interpretive
- comparative
- historical
- ontological
- relational
- editorial
- inferential

### Role

Claims are how Ma'na stores meaning without collapsing facts, interpretations, and AI inferences into one layer.

## 7. Evidence

### Definition

Evidence is any support, constraint, or challenge for a claim.

### Examples

- quoted textual span
- lexical evidence
- manuscript evidence
- historical documentation
- prior commentary
- comparative passage
- interpretive tradition

### Role

Evidence is what keeps claims reviewable rather than rhetorical.

## 8. Provenance Record

### Definition

A provenance record describes how a knowledge object came into being.

### Includes

- contributor
- source
- method
- timestamp
- process
- model or tool, if any
- review history

### Role

Provenance is required for governance, trust, reversibility, and scholarly integrity.

## 9. Contributor

### Definition

A contributor is any agent capable of producing or editing knowledge objects.

### Examples

- editor
- scholar
- curator
- translator
- reader
- AI system
- ingestion pipeline

### Role

Contributor identity is required because authorship and method affect interpretation and trust.

## 10. Tradition

### Definition

A tradition is an interpretive, scholarly, linguistic, religious, or intellectual framework within which claims acquire meaning.

### Examples

- Sufi commentary
- modern literary criticism
- philological scholarship
- classical tafsir
- existentialist reading

### Role

Tradition allows Ma'na to preserve plurality without reducing all interpretation to personal opinion.

## 11. Ontology Entity

### Definition

An ontology entity is a reusable concept in Ma'na's canonical knowledge space.

### Examples

- theme
- symbol
- concept
- human experience
- literary device
- civilization
- language
- author
- collection

### Role

Ontology entities are not generated anew for each work.

They are stable references against which works and claims can be mapped.

## 12. Relationship

### Definition

A relationship is a meaning-bearing connection between two addressable entities.

### Examples

- a claim supports another claim
- a unit evokes an ontology entity
- an interpretation challenges another interpretation
- a work belongs to a collection
- a witness derives from a source

### Role

Relationships are first-class because Ma'na is not only storing objects, but also the structure of meaning between them.

## 13. Question

### Definition

A question is a preserved inquiry that organizes discovery, interpretation, or retrieval.

### Examples

- What is exile in Ghalib?
- Why does hope intensify suffering?
- How do traditions differ in reading wine symbolism?

### Role

Questions are not merely search input.

They are durable knowledge objects that may structure commentary, graph traversal, and reader exploration.

## 14. Commentary Document

### Definition

A commentary document is a composed, human-readable knowledge package built from claims, evidence, provenance, and references.

### Role

It is a presentation and reasoning artifact, not the primitive store of truth.

This prevents the system from treating essays as opaque authoritative blobs.

## Core Relationships

The following relationships form the minimum semantic backbone of the model.

### Structural Relationships

- Source contains Witness
- Witness instantiates Work
- Witness contains Segment
- Segment may be recognized as Unit
- Work may belong to Collection
- Work may be associated with Author

### Knowledge Relationships

- Claim targets an entity
- Claim is evidenced by Evidence
- Claim has Provenance Record
- Claim may cite Source or Witness
- Claim may belong to Tradition
- Claim may support or challenge another Claim

### Ontology Relationships

- Unit may evoke Ontology Entity
- Claim may map a Unit or Work to Ontology Entity
- Ontology Entity may relate to another Ontology Entity

### Commentary Relationships

- Commentary Document is composed from Claims
- Commentary Document addresses one or more Units, Works, or Questions
- Commentary Document cites Sources, Traditions, and Contributors

### Governance Relationships

- Contributor produces Claim
- Curator reviews Claim
- Canonical registry stabilizes Ontology Entity
- Editorial process may elevate, reject, dispute, or deprecate knowledge objects

## Canonical Versus Derived Objects

The domain model must distinguish between what is fundamental and what is derivative.

### Strong Canonical Candidates

- Work
- Witness
- Unit
- Source
- Ontology Entity
- Contributor
- Tradition

These objects may become stable references.

### Governed Knowledge Objects

- Claim
- Relationship
- Commentary Document

These may be reviewed, revised, approved, disputed, or deprecated.

### Derived Objects

- AI summaries
- embeddings
- clusters
- retrieval hints
- graph projections
- recommended links
- synthesized answers

Derived objects are useful, but they must remain regenerable and non-fundamental.

## Entity Invariants

The following invariants constrain all later schemas and workflows.

### 1. A Claim Cannot Exist Without Scope

Every claim must be about something addressable.

### 2. A Claim Cannot Become Canonical Without Governance

No claim becomes reusable truth merely by being generated, repeated, or fluently expressed.

### 3. Evidence Must Remain Linkable

Evidence must remain connected to the claim it supports or challenges.

### 4. Source And Interpretation Must Remain Distinct

No commentary or AI synthesis may overwrite source material.

### 5. Witness Variation Must Remain Representable

The model must preserve differing editions, transmissions, or recensions without forcing premature unification.

### 6. Units Must Be Tradition-Aware

Unit boundaries cannot be assumed universal.

What counts as a meaningful unit may vary by language, genre, and tradition.

### 7. Ontology Entities Must Be Reusable Across Works

Ontology is global even when its application is local.

### 8. Questions Must Remain Addressable

Reader and scholarly questions should be preservable as durable objects that can gather interpretations, evidence, and cross-references over time.

## Interpretation Model Within The Domain

Interpretation is not an annotation type buried inside commentary.

It is a specialized form of claim.

### Consequences

- interpretations can disagree
- interpretations can cite evidence
- interpretations can belong to traditions
- interpretations can be reviewed
- interpretations can be compared
- interpretations can be canonical within scope without becoming universal

This is one of the most important design consequences in the entire domain model.

## Provenance Model Within The Domain

Provenance is attached to every meaningful knowledge-bearing object, especially:

- claims
- relationships
- ontology mappings
- commentary documents
- AI-generated outputs

At minimum, provenance must answer:

- who created this
- from what source
- using what method
- under what assumptions
- when
- reviewed by whom
- under which model or editorial framework

## Editorial Lifecycle

The domain model does not prescribe a UI workflow, but it does require governance states.

At minimum, knowledge-bearing objects must be able to exist in states such as:

- draft
- proposed
- reviewed
- approved
- disputed
- rejected
- deprecated

Not every entity needs every state, but the model must support explicit governance rather than implicit trust.

## Extension Mechanism

The domain model must support extension without redesign.

### Core Strategy

Use a stable universal core and allow specialized traditions or genres to extend around it.

### Universal Core

- Work
- Witness
- Segment
- Unit
- Claim
- Evidence
- Provenance
- Ontology Entity
- Relationship
- Contributor
- Tradition
- Question

### Extensions

Different literary domains may define additional semantics without replacing the core:

- poetry may define meter, rhyme, matla, maqta
- drama may define speaker, act, scene, stage direction
- scripture may define revelation context, canonical status, legal genre
- philosophy may define argument structure, proposition, objection, response
- novels may define narrative voice, chapter arc, character perspective

These are extensions of the core, not replacements for it.

## Cross-Civilizational Applicability

This model is intended to hold for:

- Ghalib
- Shakespeare
- Rumi
- Dostoevsky
- Plato
- Qur'an
- Bible
- Bhagavad Gita
- Confucius
- Nietzsche

It does so by refusing to make poem, couplet, chapter, or scripture the universal primary object.

Instead, it centers:

- source
- witness
- segment
- unit
- claim
- ontology
- provenance

These abstractions travel better across civilizations and genres than literary-form-specific assumptions.

## Example Reasoning Across Genres

### Ghalib

- Work: ghazal
- Witness: edited Diwan version
- Unit: couplet
- Claim: this couplet evokes longing
- Evidence: textual span and commentary tradition

### Shakespeare

- Work: play
- Witness: a specific edition
- Unit: speech or scene segment
- Claim: this speech dramatizes indecision
- Evidence: quoted passage and literary scholarship

### Dostoevsky

- Work: novel
- Witness: translation or original edition
- Unit: paragraph, exchange, or chapter segment
- Claim: this passage stages spiritual guilt
- Evidence: passage, narrative context, scholarly commentary

The core model remains unchanged.

## What This Domain Model Refuses

It refuses to treat:

- documents as knowledge
- commentary blobs as self-sufficient truth
- ontology tags as sufficient meaning
- AI fluency as authority
- one literary form as universal
- one tradition as final

## Consequences For The Next Document

The next architecture artifact should not yet be a full commentary schema.

The correct next step is:

`InterpretationAndProvenanceModel_v1.md`

That document should define:

- kinds of claims
- kinds of evidence
- provenance requirements
- scoped truth status
- disagreement handling
- canonical versus speculative interpretation boundaries

Only after that should Ma'na define a canonical commentary schema, because commentary is a composition of governed claims rather than a primitive domain object.
