# Ma'na Ontology And Canonicality Model v1

## Purpose

This document defines how Ma'na should treat reusable semantic entities and how such entities become stable enough for system-wide reuse.

It does not define storage, UI, schema syntax, or graph implementation.

Its goal is to answer five core questions:

- what ontology is in Ma'na
- what ontology is not
- which entities may become canonical
- how mappings become canonical
- how ontology fragmentation is prevented across traditions and civilizations

This document exists because Ma'na's value depends on distinguishing:

- reusable semantic infrastructure
- from local interpretation

Without that distinction, the system collapses into unstable tagging, inflated commentary, and inconsistent graph structure.

## Foundational Principle

Ontology in Ma'na is not a collection of convenient labels.

It is the stable semantic layer that allows knowledge to travel across:

- works
- languages
- traditions
- civilizations
- contributors
- time

Ontology should therefore be:

- reusable
- governed
- interpretable
- evidence-aware
- stable enough for coordination
- flexible enough to avoid dogmatism

## What Ontology Is

Ontology in Ma'na is the system of reusable semantic entities and relations that enable knowledge to be linked across otherwise separate literary and intellectual artifacts.

Ontology is what allows Ma'na to say, in a governed way:

- this work concerns longing
- this image instantiates wine symbolism
- this passage relates to exile
- this question belongs to the experience of waiting
- this concept is related to hope and suffering

Ontology is not the same as explanation.

It is the semantic infrastructure through which explanations can be organized, compared, and reused.

## What Ontology Is Not

Ontology in Ma'na is not:

- a freeform tag cloud
- a list of AI-generated labels
- a substitute for commentary
- a compressed summary of a poem
- a universal truth machine
- a forced flattening of traditions into one vocabulary

If ontology is treated as any of these, it will either fragment or become intellectually dishonest.

## Core Distinction: Ontology Versus Interpretation

Ontology and interpretation are deeply related, but they are not the same thing.

## Ontology

Ontology asks:

- what reusable semantic entity is being invoked?
- what stable concept or category can many works point toward?
- what relation can be traversed across the corpus?

## Interpretation

Interpretation asks:

- what does this work, unit, image, or gesture mean here?
- according to which tradition, method, or voice?
- with what tension, ambiguity, or disagreement?

## Rule

An ontology entity may be globally reusable.

Its application to a specific work or unit must remain a governed claim.

This is the most important boundary in the entire ontology model.

## Canonical Ontology Entity Classes

The following are the strongest candidates for globally reusable ontology classes.

## 1. Civilization

Used to locate works, traditions, and intellectual lineages within broad civilizational frames.

### Examples

- Persian
- Arabic
- Urdu
- English
- Sanskrit
- Greek

## 2. Language

Used for source description, lexical reasoning, and multilingual normalization.

### Examples

- Urdu
- Persian
- Arabic
- English

## 3. Author

Used for stable attribution and corpus traversal.

### Examples

- Ghalib
- Rumi
- Shakespeare
- Iqbal

## 4. Collection

Used to group works under stable editorial or historical containers.

### Examples

- Diwan-e-Ghalib
- Kulliyat-e-Iqbal
- Sonnets

## 5. Work Form

Used to classify broad literary form without overfitting all meaning to the form itself.

### Examples

- ghazal
- sonnet
- play
- novel
- sermon
- dialogue
- essay

## 6. Unit Form

Used to classify meaning-bearing units recognized within specific traditions or genres.

### Examples

- couplet
- stanza
- scene
- ayah
- chapter segment
- dialogue turn

This category must remain flexible because unit boundaries are tradition-aware.

## 7. Vocabulary Entity

A reusable lexical or semantic word-level object.

### Examples

- hijr
- saqi
- ishq

Vocabulary entities are not merely tokens.

They are governed lexical knowledge objects.

## 8. Theme

A broad recurring semantic field.

### Examples

- love
- death
- time
- memory
- beauty

Themes must remain broad enough for cross-work reuse and precise enough to remain meaningful.

## 9. Human Experience

A more lived, existential, or psychological semantic class than theme.

### Examples

- longing
- grief
- waiting
- loneliness
- exile
- wonder

Human Experience is one of Ma'na's most important ontology classes because it aligns directly with the platform's purpose.

## 10. Symbol

A reusable symbolic object or image whose meanings vary by context and tradition.

### Examples

- wine
- mirror
- candle
- desert
- ocean

Symbols must allow multiple interpretations.

The symbol entity is canonical.

Its meanings are not.

## 11. Concept

A reusable abstraction that may recur across works and civilizations.

### Examples

- selfhood
- nothingness
- reality
- illusion
- divine love

Concept entities must remain distinguishable from temporary interpretive phrasing.

## 12. Literary Device

A reusable rhetorical or literary mechanism.

### Examples

- paradox
- irony
- metaphor
- hyperbole
- ambiguity

## 13. Tradition

Although tradition is already a core domain entity, it is also ontologically important because many claims and symbol meanings remain unintelligible without it.

### Examples

- Sufi
- modern literary critical
- philological
- classical tafsir

## Ontology Entity Criteria

An entity should qualify for ontology only if it satisfies most of the following:

- reusable across multiple works
- meaningful beyond one single passage
- stable enough to govern consistently
- understandable without being tied to one commentary voice
- distinct enough from adjacent entities
- likely to matter for retrieval, comparison, or graph traversal

If something fails these tests, it is more likely an interpretation, descriptor, or note than an ontology entity.

## Ontology Entity Criteria For Rejection

An entity should not become canonical ontology merely because:

- it appears in one poem
- it sounds insightful
- an AI proposed it
- it is fashionable terminology
- it is a temporary editorial convenience
- it compresses a whole interpretation into a pseudo-concept

## Stable Entity Versus Local Mapping

The ontology model must distinguish two things:

## 1. Stable Entity

A reusable semantic object in the canonical registry.

### Example

- `longing`
- `wine`
- `selfhood`

## 2. Local Mapping Claim

A governed claim that a specific unit, work, or commentary invokes that entity.

### Example

- this couplet evokes `longing`
- this image instantiates `wine`
- this passage maps to `selfhood`

The entity may be canonical.

The mapping remains local, scoped, reviewable, and contestable.

## Canonicality Model

## 1. What Canonical Means Here

Canonical ontology means:

- stable enough for reuse
- approved for reference
- safe enough for system-wide linking
- governed enough to prevent uncontrolled duplication

Canonical does not mean:

- final
- universally true
- beyond challenge
- equally applicable to every tradition

## 2. Levels Of Canonicality

Ma'na should conceptually support multiple levels of stability.

### Proposed

A candidate entity or mapping awaiting governance.

### Approved

Stabilized for internal use and consistent editorial reference.

### Canonical

Stable enough for broad reuse across ingestion, retrieval, commentary, and graph construction.

### Deprecated

Previously used, now retained for history and backward traceability but no longer preferred.

## 3. Canonical Within Scope

Some ontology decisions may be canonical only within a scope.

### Examples

- canonical for a tradition
- canonical for a language-specific lexical frame
- canonical for house editorial policy

This is legitimate so long as the scope remains visible.

## Mappings And Their Governance

## 1. Mapping Is A Claim, Not A Fact

Any assignment from work or unit to ontology entity is a claim.

That claim may be:

- supported
- contested
- approved
- disputed
- inferred

It must never be hidden as though ontology itself produced the mapping automatically.

## 2. Mapping Classes

At minimum, mappings may involve:

- unit to theme
- unit to human experience
- unit to symbol
- unit to concept
- work to theme
- work to human experience
- work to concept
- vocabulary entity to concept
- symbol to interpretive meaning

## 3. Mapping Evidence

Mappings should require some combination of:

- textual evidence
- lexical evidence
- commentary evidence
- tradition evidence
- comparative evidence
- AI proposal with human review

## 4. High-Impact Mapping Rule

The more a mapping affects retrieval, recommendation, graph structure, or canonical commentary, the stronger the review requirement should be.

## Symbol Model

Symbols deserve special treatment because they are highly reusable but highly unstable.

## 1. Symbol Entity

The symbol itself may be canonical.

### Example

- wine

## 2. Symbol Meanings

The meanings of a symbol should not collapse into the symbol entity itself.

### Example

`wine` may carry meanings such as:

- divine grace
- intoxication
- ecstasy
- forbidden pleasure
- poetic inspiration
- mystical knowledge

These are not identical and should not be merged into one canonical meaning.

## 3. Rule

Canonicalize the symbol entity.

Govern the symbol interpretations as claims.

This same logic often applies to other semantically rich ontology classes.

## Human Experience Model

Human Experience is central to Ma'na's reader experience and philosophical mission.

It should be treated as a primary ontology family rather than an afterthought beneath themes.

## Distinction From Theme

Theme is broad and literary.

Human Experience is lived and existential.

### Examples

- `love` may be a theme
- `longing` may be a human experience
- `memory` may be a theme
- `exile` may be a human experience

The boundary will not always be perfect, but the distinction is still useful and worth preserving.

## Concept Model

Concept entities should be used for abstractions that remain durable across traditions and support deeper graph reasoning.

### Examples

- selfhood
- illusion
- freedom
- mortality
- divine love

Concepts should not absorb every interesting sentence.

If a candidate entity is really a whole interpretation compressed into a noun phrase, it should remain a claim rather than ontology.

## Vocabulary Model

Vocabulary entities are important because Ma'na spans languages and traditions.

Vocabulary should not be reduced to tokenization.

Vocabulary entities may include:

- lexical identity
- root
- language
- semantic range
- historical usage
- related words

Vocabulary entities should be linkable to themes, concepts, and symbols without becoming identical to them.

## Ontology Fragmentation Risks

The ontology layer is especially vulnerable to fragmentation.

The main causes are:

- freeform tagging
- duplicate entities with minor wording differences
- importing AI proposals directly
- over-specific entities that belong only to one work
- flattening tradition-specific meanings into one entity
- mixing interpretation phrases with ontology entities

## Anti-Fragmentation Principles

To resist fragmentation, Ma'na should preserve the following rules.

### 1. Reuse Before Creation

Every new mapping process should first attempt to connect to an existing ontology entity.

### 2. New Entity Creation Must Be Explicit

A proposed new entity should always remain visible as a proposal until reviewed.

### 3. Aliases Must Not Create New Entities Automatically

Different labels may refer to the same ontology entity.

Alias resolution should be governed.

### 4. Interpretation Should Not Be Canonicalized As Entity

If the candidate is actually a contextual reading, it should stay a claim.

### 5. Tradition-Specific Meaning Must Be Scoped

The same entity may carry different meanings across traditions without requiring ontological duplication.

## Cross-Civilizational Neutrality

Ontology should not inherit the assumptions of a single canon.

This requires:

- no single language as semantic default
- no single religion as symbolic default
- no single literary form as unit default
- no single commentary tradition as interpretive authority

Ontology should be broad enough to connect civilizations without erasing difference.

## Graph Core Boundary

The knowledge graph should not be built from arbitrary textual co-occurrence.

The graph core should emerge from governed ontology and relation claims.

## Graph-Suitable Relations

The following are good candidates for graph-core relations, provided they remain governed:

- evokes
- belongs to
- resembles
- contrasts with
- derives from
- supports
- challenges
- interpreted as
- associated with

## Relation Principle

A relation belongs in the graph core only if:

- it has reusable semantic value
- it is evidence-aware
- it is not merely temporary UI convenience
- it can survive beyond a single commentary artifact

## Canonical Registry Principles

The canonical registry is the governance mechanism for ontology stability.

Its role is to:

- preserve stable semantic references
- prevent uncontrolled duplication
- support reuse across ingestion
- keep aliases and deprecations traceable
- allow evolution without historical amnesia

The registry should not be treated as a prison.

It should be a disciplined memory of what the system has stabilized.

## What Should Enter The Registry

The strongest candidates are:

- themes
- human experiences
- symbols
- concepts
- literary devices
- civilizations
- languages
- authors
- collections
- work forms
- unit forms
- vocabulary entities
- traditions

## What Should Not Enter Automatically

The following should not enter the registry automatically:

- AI-proposed labels
- one-off interpretive phrases
- unresolved commentary abstractions
- speculative equivalences
- unstable draft mappings

## Curator Responsibilities In Ontology

Curators are responsible for governance, not arbitrary control.

At minimum, ontology governance should support the following actions:

- approve
- reject
- merge
- split
- rename
- alias
- deprecate
- restore

These actions should be visible because ontology decisions affect the entire downstream system.

## Relationship To Commentary

Commentary uses ontology, but commentary is not ontology.

Commentary explains, tensions, compares, and teaches.

Ontology stabilizes reusable semantic reference points.

The future commentary schema should therefore:

- reference ontology entities
- never reduce itself to ontology tags
- preserve claim-level nuance beyond ontology assignment

## Relationship To AI

AI may:

- propose ontology candidates
- suggest mappings
- cluster similar entities
- recommend merges
- identify possible duplicates

AI must not:

- finalize ontology entities autonomously
- finalize canonical mappings autonomously
- erase tradition-specific differences
- convert speculative label suggestions into stable ontology

## Minimum Invariants

Any future ontology implementation violates this model if it:

- treats mappings as facts instead of claims
- stores interpretation as ontology entity
- canonicalizes AI labels automatically
- erases disagreement in symbol meaning
- duplicates entities due to wording drift
- uses ontology as a substitute for commentary
- makes one civilization's semantics the default for all others

## Consequence For The Next Document

The next architecture artifact should be:

`CanonicalCommentarySchema_v1.md`

That document should define how commentary documents are composed from:

- governed claims
- scoped interpretations
- evidence references
- provenance records
- ontology links
- visible disagreement

Only now is Ma'na ready to define a final commentary schema, because the domain, interpretation, and ontology layers are now separated clearly enough to avoid conceptual collapse.
