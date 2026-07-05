# PoemSpecification

This document defines the canonical structure of a single poem in Maana.

It is the most important editorial specification in the repository because it influences:

- editorial workflow
- content model
- CMS requirements
- database design
- API contracts
- UI structure
- search behavior
- future AI grounding

Implementation documents may not redefine this structure. They must inherit from it.

## Purpose

The goal is not to specify one thousand poems abstractly.
The goal is to prove that one poem can be represented completely and rigorously.

Once one poem can be modeled well, the rest of the system becomes a question of scaling
the same structure.

## Canonical Sections

Every poem record should be able to contain the following sections, even if some are empty
at early editorial stages.

### 1. Identity

- canonical title
- alternate titles
- poem ID
- poet
- source tradition
- source language
- form
- meter when known
- date or period when known

### 2. Source Text

- original script
- normalized text if needed
- verse segmentation
- line numbering or couplet numbering
- source edition

### 3. Translation Layer

- literary translation
- literal translation
- transliteration when needed
- translator attribution
- translation notes

### 4. Word Annotation Layer

- word-by-word meanings
- grammar notes when relevant
- morphology when useful
- ambiguity notes for key terms

### 5. Ontology Layer

- human questions
- human experiences
- themes
- symbols
- concepts
- literary devices

All ontology tags must reference canonical ontology definitions rather than inventing new ones.

### 6. Commentary Layer

- summary interpretation
- historical context
- literary commentary
- mystical commentary
- philosophical commentary
- psychological commentary
- competing interpretations

### 7. Relationship Layer

- related poems
- related poets
- related symbols
- related themes
- cross-civilization parallels
- response or influence relationships

### 8. Evidence Layer

Every substantive claim should be traceable to an evidence class.

Examples:

- original text evidence
- translator interpretation
- classical commentary
- modern scholarship
- editorial synthesis

### 9. Citation Layer

- source edition citations
- translation citations
- commentary citations
- scholarly citations
- reference article citations
- audio or recitation citations when applicable

### 10. Editorial Metadata

- coverage level
- quality level
- editorial status
- reviewer status
- version history
- last updated date

## Canonical Example Shape

```yaml
poem:
  title: [canonical title]
  poet: [poet]
  source_language: [language]
  form: [ghazal|qasida|sonnet|haiku|other]
  source_text:
    verses: []
  translations:
    literary: []
    literal: []
  annotations:
    words: []
    grammar: []
  ontology:
    human_questions: []
    human_experiences: []
    themes: []
    symbols: []
    concepts: []
    literary_devices: []
  commentary:
    historical: []
    literary: []
    mystical: []
    philosophical: []
    psychological: []
  evidence: []
  citations: []
  editorial:
    coverage_level: null
    quality_level: null
    status: draft
```

## Scope Rule

Not every poem must be complete at first.
But every poem must fit this canonical structure so that the library can grow without
changing its underlying model.
