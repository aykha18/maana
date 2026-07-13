# Diwan-e-Ghalib Pilot

This pilot defines how to test Ma'na on the first 10 real poems from `Diwan-e-Ghalib`.

## Goal

Prove that the ontology-first architecture works on real poem data before scaling to the full collection.

## Why Start With 10 Poems

- Small enough for manual review
- Large enough to expose ontology fragmentation
- Large enough to test recurring symbols, concepts, and experiences
- Small enough to support curator-first iteration

## Scope For The Pilot

Use exactly one authoritative source edition for all 10 poems.

Each pilot poem should include:

- canonical title or conventional label
- poet
- collection
- source language
- poetic form
- original text
- verse or couplet segmentation
- source citation
- optional translation

## Recommended Test Shape

Do not start by sending the 10 poems through the current lecture pipeline.

The current implemented pipeline is lecture-first.
For poems, use a direct structured-input pilot.

### Phase P1: Source Dataset

Create a single structured dataset for 10 poems with:

- poem ID
- collection ID
- author ID
- edition metadata
- couplet-level text
- optional translation
- optional commentary references

### Phase P2: Canonical Resolution

For each poem, attempt to resolve:

- author
- collection
- language
- literary work
- literary unit
- themes
- human experiences
- symbols
- concepts

Expected result:

- known entities map to the canonical registry
- unknown entities are marked `proposed_new`
- nothing becomes canonical automatically

### Phase P3: Curator Review

For each proposed entity, curator decides:

- approve existing match
- reject
- merge into existing entity
- rename
- create new canonical entity

### Phase P4: Evaluation

Measure:

- canonical match rate
- number of `proposed_new` entities
- number of false matches
- curator review time per poem
- ontology collisions across the 10 poems

## Success Criteria

The 10-poem pilot is successful if:

- all 10 poems fit the canonical poem structure
- no canonical entities are invented silently
- provenance is preserved for all substantive tags
- proposed ontology entities are reviewable in a curator workflow
- the same recurring symbol or concept resolves consistently across poems

## Practical Next Step

Use the new canonical registry seed as the starting ontology.

Then prepare a manual pilot dataset with 10 poems from one edition of `Diwan-e-Ghalib`.

Recommended first poem fields:

```json
{
  "poem_id": "ghalib-001",
  "title": "",
  "author": "Ghalib",
  "collection": "Diwan-e-Ghalib",
  "source_language": "Urdu",
  "form": "Ghazal",
  "literary_unit": "Couplet",
  "source_edition": "",
  "verses": [
    {
      "unit_number": 1,
      "text": ""
    }
  ],
  "translations": [],
  "commentary_references": []
}
```

## What To Build Next

1. poem source models
2. poem input dataset schema
3. canonical resolver integration over poem ontology tags
4. curator review queue for proposed entities
