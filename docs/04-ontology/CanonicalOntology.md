# CanonicalOntology

This document is the constitutional layer of Maana.

It defines the canonical meaning of the major entities, relationships, and editorial rules
that shape the platform. Database tables, API contracts, search logic, reference content,
and future AI behavior should all derive from this ontology.

## Priority Order

The repository should be developed in this order:

1. Knowledge
2. Ontology
3. Editorial rules
4. Database
5. API
6. Frontend
7. AI

Technology serves the knowledge model, not the other way around.

## Ontology Order

Within the ontology itself, the modeling order should be:

1. Human questions
2. Human experiences
3. Themes
4. Symbols
5. Concepts
6. Poems
7. Verses
8. Words
9. Knowledge graphs

This makes the platform fundamentally about the questions that unite humanity,
with poetry acting as one of the richest ways those questions are explored.

## Core Principle

Maana is best understood as a publishing platform with software attached.
Its deepest asset is not code. Its deepest asset is structured literary knowledge.

## Canonical Entities

### Human Question

A human question is a universal question that human beings ask across civilizations,
traditions, and eras.

Examples include:

- What is love?
- Why do we suffer?
- What is death?
- Why does God feel distant?
- What is beauty?
- Is freedom possible?

Human questions sit above human experiences, themes, and symbols.
They explain why discovery should work across languages and traditions even when poems
do not share vocabulary.

### Poet

A poet is the author or attributed source of one or more poems.

### Poem

A poem is the primary literary work being interpreted, translated, linked, and explored.

### Verse

A verse is the smallest canonical textual unit modeled for reading, annotation,
translation, and relationship mapping.

### Word

A word is the smallest lexical unit that may require meaning, history, grammar,
or interpretive notes.

### Human Experience

A human experience is a broad lived condition or existential state used to organize
poetry across cultures.

Examples include:

- love
- grief
- exile
- hope
- mortality
- faith

Human experiences are responses to or embodiments of human questions.
They are broader than themes and provide major discovery entry points.

### Theme

A theme is a recurring literary, philosophical, or spiritual idea expressed within a poem
or verse.

Examples include:

- unrequited love
- divine love
- impermanence
- surrender
- remembrance

A theme is narrower and more analytical than a human experience.

### Symbol

A symbol is a concrete image, object, person, or motif that carries layered meaning
through repeated literary use.

Examples include:

- wine
- rose
- mirror
- candle
- dust
- beloved

A symbol can be literal, metaphorical, mystical, political, or psychological at the same
time. The model must allow multiple dimensions of meaning without collapsing them into one.

### Motif

A motif is a repeated literary pattern or recurrence that may involve symbols, settings,
actions, or situations.

A motif is not identical to a symbol.

- A symbol is usually a meaning-bearing image or object.
- A motif is a repeated pattern or recurrence across works.

### Concept

A concept is an abstract idea used to connect themes, symbols, commentary, and experiences.

Examples include:

- absence
- memory
- ego
- transcendence
- impermanence

### Commentary

Commentary is editorial interpretation that helps the reader understand a poem, verse,
symbol, or concept.

Commentary is trustworthy when it is:

- grounded in the text
- clear about what is evidence versus interpretation
- historically and culturally aware
- citation-friendly
- consistent with editorial standards

## Four-Layer Distinction

The platform should distinguish four different layers clearly:

### Human Question

The universal question being asked.

Examples:

- What is love?
- Why do humans suffer?
- What survives death?

### Human Experience

What a person feels or undergoes.

Examples:

- longing
- hope
- loss
- wonder

### Theme

What the poem discusses or develops intellectually.

Examples:

- separation
- mortality
- divine love
- exile

### Symbol

How the poem expresses its meanings through image or motif.

Examples:

- wine
- rose
- dust
- mirror

## Key Distinctions

### Human Question vs Human Experience

- Human question is universal and interrogative.
- Human experience is lived and felt.
- Multiple experiences can gather around one question.

Example:

- Human question: What is love?
- Human experience: longing
- Human experience: devotion
- Human experience: grief

### Human Experience vs Theme

- Human experience is broader and reader-facing.
- Theme is narrower and interpretive.
- A poem can map to multiple themes inside one larger human experience.

Example:

- Human experience: love
- Theme: unrequited love
- Theme: divine love
- Theme: remembered love

### Theme vs Symbol

- Theme expresses an idea.
- Symbol carries meaning through an image.

Example:

- Theme: impermanence
- Symbol: dust

### Symbol vs Motif

- Symbol is a meaning-bearing element.
- Motif is a repeated literary pattern.

Example:

- Symbol: mirror
- Motif: reflection and self-recognition recurring across poets

## Meaning Dimensions

The ontology should support multiple meaning dimensions for the same object.

For symbols and concepts, the model should be able to record:

- literal dimension
- metaphorical dimension
- mystical dimension
- psychological dimension
- philosophical dimension
- political dimension
- civilization-specific usage
- poet-specific usage

## Canonical Relationship Rules

The graph should treat relationships as first-class knowledge.

Examples:

- human question gives rise to human experience
- human experience contains theme
- poet wrote poem
- poem contains verse
- poem expresses theme
- poem evokes human experience
- poem responds to human question
- poem uses symbol
- symbol relates to concept
- theme belongs to human experience
- commentary interprets poem
- translation renders poem
- poet influenced poet

All relationships should be explicit, explainable, and editorially meaningful.

## Question Graph

One critical layer of the ontology is the Question Graph.

This layer connects human questions to the many ways they are explored across poems,
experiences, themes, symbols, and commentary.

It should support queries like:

- Why do humans fear death?
- Can love survive separation?
- Why does God feel absent?

## Human Experience Graph

The Human Experience Graph is a special layer of the knowledge graph that allows readers
to discover poems through lived experience rather than only text or author metadata.

Each poem should eventually support structured annotations like:

```yaml
primary_experience:
  - Longing
secondary_experiences:
  - Hope
  - Regret
emotional_tone:
  - Melancholic
  - Reflective
existential_questions:
  - What is love?
  - Why do humans suffer?
mystical_dimension:
  - Separation from the Divine
psychological_dimension:
  - Attachment
  - Desire
philosophical_dimension:
  - Impermanence
symbols:
  - Wine
  - Night
  - Dust
literary_devices:
  - Irony
  - Hyperbole
```

This is what enables experience-first discovery across languages and civilizations.
Together, the Question Graph and Human Experience Graph make the platform more powerful
than simple theme tagging or full-text search.

## Intellectual Architecture

The conceptual flow should be:

1. Human question
2. Human experience
3. Theme
4. Symbol
5. Concept
6. Poem
7. Verse
8. Word
9. Literary knowledge graph
10. Database
11. API
12. Frontend
13. AI

The database implements this architecture. It does not define it.

## Implementation Boundary Rule

No implementation-facing document may define a concept.

This means:

- `08-data-model/` may reference ontology terms but must not redefine them.
- `09-search/` may reference ontology terms but must not redefine them.
- `10-api/` may reference ontology terms but must not redefine them.
- `06-user-experience/` may reference ontology terms but must not redefine them.
- backend and frontend documents must inherit ontology definitions rather than inventing new ones.

`04-ontology/CanonicalOntology.md` is the authoritative source for first-class concepts.

## Editorial Consequences

Editorial work should answer definitional questions before scaling content:

- What qualifies as a theme?
- When is something a symbol instead of a motif?
- How should contradictory readings be recorded?
- What makes commentary reliable?
- How do civilization-specific meanings coexist?

## Scope Rule

When there is ambiguity, prefer richer structure over flatter categories.

If a concept matters to discovery, explanation, comparison, search, or future AI behavior,
it should be modeled explicitly in the ontology.
