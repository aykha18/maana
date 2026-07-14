# Ma'na Canonical Commentary Schema v1

## Purpose

This document defines the canonical structure for commentary in Ma'na.

It is not a database schema, API payload, or storage prescription.

Its role is to define the minimum composition rules that every commentary artifact in Ma'na should follow so that the corpus remains coherent across:

- Ghalib
- Iqbal
- Rumi
- Shakespeare
- Dostoevsky
- Qur'an
- philosophy
- drama
- prose
- oral traditions

This schema is derived from:

- [FirstPrinciplesOfMaana.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/FirstPrinciplesOfMaana.md)
- [CoreDomainModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/CoreDomainModel_v1.md)
- [InterpretationAndProvenanceModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/InterpretationAndProvenanceModel_v1.md)
- [OntologyAndCanonicalityModel_v1.md](file:///c:/Users/Ayub/Documents/trae_projects/maana/docs/18-roadmap/OntologyAndCanonicalityModel_v1.md)

## Foundational Principle

Commentary in Ma'na is not the primitive store of truth.

Commentary is a composed knowledge artifact built from governed parts:

- addressable scope
- claims
- evidence
- provenance
- ontology links
- disagreement visibility
- editorial status

This means Ma'na should never treat commentary as an opaque essay blob whose authority cannot be audited.

## What Commentary Is

Commentary is a structured human-readable and AI-readable explanation layer attached to one or more addressable objects.

Those objects may include:

- work
- witness
- unit
- question
- cross-work cluster

Commentary exists to:

- explain
- compare
- teach
- contextualize
- surface tensions
- preserve interpretive plurality

## What Commentary Is Not

Commentary is not:

- ontology itself
- source text itself
- a list of flat tags
- a substitute for evidence
- a substitute for provenance
- a single authoritative truth voice
- a mandatory fixed essay template for every tradition

## Commentary Scope

Every commentary artifact must declare its scope.

At minimum, commentary may be scoped to:

- a work
- a witness
- a unit
- a question
- a thematic cluster

### Rule

No commentary may exist without a clearly addressable subject.

## Commentary Granularity

The schema must support multiple levels of commentary without redesign.

### 1. Unit Commentary

Commentary attached to a meaning-bearing unit.

### Examples

- a couplet
- a stanza
- a scene
- a paragraph
- an ayah
- a passage

### 2. Work Commentary

Commentary attached to a whole work.

### Examples

- an entire ghazal
- a play
- a chaptered philosophical work
- a sermon

### 3. Question-Centered Commentary

Commentary organized around a durable question rather than one work alone.

### Examples

- what is exile?
- why does hope intensify suffering?
- how is wine interpreted across traditions?

### 4. Comparative Commentary

Commentary addressing more than one work, unit, or tradition together.

## Core Commentary Object

Every canonical commentary artifact should be understood as containing the following conceptual parts.

## 1. Identity

Defines what this commentary artifact is.

### Includes

- commentary identity
- commentary type
- addressed object or objects
- language of commentary
- contributor identity
- current editorial status

## 2. Addressed Scope

Defines precisely what part of the corpus this commentary is about.

### Examples

- one unit
- multiple units from one work
- one work
- a specific witness
- a question spanning many works

## 3. Source Anchoring

Commentary must preserve visible connection to the source material it discusses.

### Includes

- cited source or witness
- cited segment or unit references
- quoted or summarized evidence spans

### Rule

Commentary may interpret source material, but must not overwrite it.

## 4. Commentary Claims

This is the heart of the commentary object.

Commentary is composed from governed claims, not a single undifferentiated essay.

### Claim Families Commonly Used In Commentary

- literal or textual clarification
- descriptive observation
- paraphrastic explanation
- symbolic reading
- emotional reading
- psychological reading
- existential reading
- mystical reading
- philosophical reading
- comparative reading
- pedagogical reflection
- synthetic summary

### Rule

These claim families are available modes, not mandatory blocks for every commentary.

## 5. Evidence Attachments

Each substantial commentary claim should retain its evidence base or evidence posture.

### Possible Evidence Inputs

- textual quotation
- lexical note
- witness comparison
- historical context
- scholarly reference
- tradition-based support
- comparative passage

## 6. Provenance

Every commentary artifact must declare how it came into being.

### Includes

- contributor
- contributor class
- method
- source basis
- timestamp
- review lineage
- AI involvement, if any

## 7. Ontology Links

Commentary may link to ontology entities, but those links remain governed mappings, not hidden facts.

### Typical Ontology Families

- theme
- human experience
- symbol
- concept
- literary device
- vocabulary entity

## 8. Disagreement And Multiplicity

Commentary must be able to preserve:

- alternative readings
- contested claims
- tradition-specific interpretations
- uncertainty
- unresolved tensions

### Rule

If disagreement exists, commentary should surface it explicitly rather than compressing it into one falsely unified explanation.

## 9. Reader Value Layer

Commentary may include pedagogical or reflective material intended for the reader.

### Examples

- reflection questions
- practical framing
- interpretive tensions
- suggested cross-references

This layer is useful, but it must remain distinguishable from stronger evidentiary claims.

## Required Commentary Sections

Every canonical commentary artifact should contain the following minimum sections conceptually, even if presentation differs by interface.

## 1. Commentary Header

Must identify:

- what is being commented on
- commentary type
- contributor or contributor class
- status
- scope

## 2. Source Reference Block

Must identify:

- source or witness basis
- relevant unit or segment references
- quoted or referenced textual anchors

## 3. Core Explanation Block

Must contain at least one governed explanatory claim set.

This may be:

- literal clarification
- paraphrastic explanation
- descriptive reading
- interpretive explanation

## 4. Evidence Or Evidence Posture Block

Must indicate, at minimum:

- direct evidence
- supporting evidence types
- or explicit evidence posture if fully expanded evidence is not yet rendered

## 5. Provenance Block

Must indicate:

- authorship or generating agent
- method
- review condition
- AI involvement, if any

## 6. Status And Disagreement Block

Must indicate:

- editorial state
- truth status where applicable
- whether the artifact contains contested or tradition-specific material

## Optional Commentary Sections

The following sections are strongly useful, but should remain optional to avoid forcing one literary form or one interpretive tradition onto all commentary.

## 1. Vocabulary Notes

Useful where lexical difficulty or semantic density is important.

## 2. Symbolic Reading

Useful where imagery carries layered meaning.

## 3. Emotional Reading

Useful where affective experience matters to explanation.

## 4. Psychological Reading

Useful where the work stages interior conflict, attachment, longing, obsession, memory, guilt, or self-deception.

## 5. Existential Reading

Useful where the text engages freedom, suffering, mortality, meaning, exile, faith, or despair.

## 6. Mystical Reading

Useful only where such a reading is relevant and properly scoped to tradition.

It must not be treated as the default mode for all literature.

## 7. Philosophical Reading

Useful where conceptual comparison or argument structure matters.

## 8. Literary Analysis

Useful where rhetoric, imagery, irony, paradox, ambiguity, or structure materially affect meaning.

## 9. Historical Context

Useful where transmission, biography, or period context changes interpretation.

## 10. Comparative References

Useful where cross-work or cross-tradition comparison deepens understanding.

## 11. Reflection Questions

Useful for reader guidance, provided they remain clearly pedagogical and not disguised claims of fact.

## Commentary Types

The schema should support multiple commentary types under one universal contract.

## 1. Canonical Commentary

The principal stable commentary artifact for a work, unit, or question.

This is the most curated and reusable form.

## 2. Tradition-Specific Commentary

A commentary artifact explicitly situated in a tradition.

### Examples

- Sufi reading
- philological reading
- literary-critical reading
- theological reading

## 3. Scholarly Commentary

A commentary artifact grounded in attributed scholarship.

## 4. AI-Assisted Commentary

A commentary artifact whose composition involved AI, but whose provenance and review path remain explicit.

## 5. Pedagogical Commentary

A commentary artifact optimized for teaching and reader guidance.

## Rule

These types may overlap, but the artifact must declare which mode or modes it inhabits.

## Commentary Composition Rules

## 1. Composition Over Monolith

Commentary should be composed from claim sets rather than stored only as a single unstructured paragraph.

## 2. Human-Readable And Machine-Readable

Commentary must remain readable to humans, but structured enough that AI systems can:

- trace evidence
- compare interpretations
- surface disagreement
- synthesize responsibly

## 3. No False Completeness

If a commentary lacks a mode of interpretation, it should simply omit it rather than generating filler.

Absence is preferable to shallow completion.

## 4. No Hidden Canonicalization

If commentary includes ontology mappings or interpretive conclusions, their status must remain visible.

## 5. No Provenance Loss

If commentary is summarized, translated, synthesized, or adapted, provenance must remain traceable to its underlying claims and sources.

## Commentary Status Model

Commentary artifacts should support explicit governance states.

### Editorial States

- draft
- proposed
- reviewed
- approved
- disputed
- deprecated

### Epistemic Notes

The commentary artifact may also indicate when it contains:

- contested claims
- tradition-specific claims
- speculative claims
- AI-generated sections

These should not be hidden behind one approval label.

## Commentary And Truth

Commentary should not present itself as raw truth.

Instead, a commentary artifact should present:

- what is directly grounded
- what is interpretive
- what is tradition-specific
- what is uncertain
- what is contested

This is one of the defining differences between Ma'na and a conventional explanation system.

## Commentary And Ontology

Commentary may reference ontology, but should never collapse into ontology-only output.

### Good Use

- linking a unit to `longing`
- linking a symbol reading to `wine`
- identifying `paradox` as a literary device

### Bad Use

- replacing explanation with tags
- presenting ontology labels as sufficient interpretation
- hiding contested mappings inside polished prose

## Commentary And Questions

Commentary in Ma'na should support question-driven navigation.

This means the schema should allow commentary to address not only source objects, but also durable human questions.

### Examples

- Why does longing persist?
- Why does certainty sometimes wound more than ambiguity?
- What makes exile inward rather than geographical?

This matters because Ma'na is building not only a literature corpus, but a map of human consciousness through literature.

## Cross-Genre Neutrality

This schema must work across:

- poetry
- drama
- prose
- scripture
- philosophy
- essays
- letters
- oral traditions

It therefore must not require:

- couplets
- stanza structure
- rhyme discussion
- mystical interpretation
- literary-device commentary
- translation layers in every case

These may be present where relevant, but they are not universal structural requirements.

## Extension Mechanism

The canonical commentary schema should use a stable core plus optional extensions.

## Stable Core

- identity
- scope
- source anchoring
- claim sets
- evidence posture
- provenance
- ontology links
- status
- disagreement visibility

## Extensions

Different domains may add commentary extensions:

- poetry: meter, matla, maqta, rhyme, prosody
- drama: speaker, act, scene, performance context
- scripture: revelation context, jurisprudential relevance, doctrinal history
- philosophy: proposition, objection, response, conceptual lineage
- prose: narrative perspective, character interiority, chapter arc

These enrich the schema without replacing the universal core.

## Example Universal Shape

The following is conceptual rather than technical:

1. Identify the commentary object and what it addresses.
2. Anchor it to source or witness references.
3. Present one or more claim groups.
4. Show evidence or evidence posture for substantial claims.
5. Preserve provenance and method.
6. Show ontology links where relevant.
7. Surface disagreement, uncertainty, or scope.
8. Optionally provide reader-facing reflection or comparison.

## Minimum Invariants

Any future implementation violates this schema if it:

- stores commentary with no addressable scope
- stores commentary with no source anchoring
- stores interpretation with no provenance
- hides disagreement inside polished synthesis
- replaces explanation with flat ontology labels
- presents AI-generated commentary as if it were unattributed human scholarship
- forces every literary tradition into one fixed essay template

## Recommendation For Implementation Sequence

This schema should guide, but not yet freeze, technical implementation.

The next practical architecture artifact after this should be one of:

- `RetrievalAndStorageArchitecture_v1.md`
- `EditorialWorkflowAndVersioning_v1.md`

If the immediate goal is product behavior, the stronger next step is:

`EditorialWorkflowAndVersioning_v1.md`

because commentary quality and canonicality depend as much on review workflow as on schema design.
