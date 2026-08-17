# Maana Specs

This repository is the specification layer for Maana.

The project is knowledge-first. Before building software, we define the ideas, entities,
relationships, editorial principles, and decisions that give the product its intellectual
shape.

Maana now has two explicit product responsibilities:

- help readers discover meaning in poetry
- help readers cultivate the capacity to discover meaning

## Purpose

- Provide a single source of truth for product intent and scope.
- Define the domain model before implementation.
- Turn literary understanding into structured knowledge.
- Keep future backend, frontend, CMS, and AI work aligned.

## Name

`Maana` is derived from `ma'na` (معنى), meaning significance or that which lies
behind words. It exists as a live concept across Arabic, Persian, and Urdu literary
traditions.

The name fits the product because readers do not come only to consume text.
They come to discover what the text means.

## Working Principle

The order of work is:

1. Knowledge
2. Ontology
3. Editorial rules
4. Database
5. API
6. Frontend
7. AI

Technology serves the intellectual model, not the other way around.

## Current Focus

- `00-overview/`
- `01-philosophy/`
- `03-domain/`
- `04-ontology/`
- `10-api/`
- `11-backend/`
- `13-editorial/`
- `18-roadmap/`
- `20-decisions/`
- `21-research/`
- `23-reference/`

## Current Strategy

The work now runs on three parallel tracks:

1. **Semantic Infrastructure track**: build the World, Chapter, Cluster, and agent system that makes Ma'ana self-organizing.
2. **Ontology track**: refine `04-ontology/CanonicalOntology.md` carefully over time.
3. **Editorial track**: define how one poem is represented, annotated, evidenced, cited,
   versioned, and quality-graded.

## Near-Term Milestones

### Semantic Infrastructure (Phase 0)

Before literary implementation begins, the repository should have a working semantic engine:

- 105 existing Worlds migrated to canonical PostgreSQL + Neo4j + pgvector
- Agent system operational (Ingestion, Relation, Architect, Ring, Gap, Quality)
- Semantic Projection Service keeping stores in sync
- Human-in-the-loop approval workflow for architectural changes

### Literary Knowledge (Phase 6)

Before implementation begins, the repository should be able to specify one poem completely.

That means one poem should have a complete specification for:

- metadata
- original text
- translations
- word annotations
- themes and symbols
- commentary
- evidence classes
- citations
- editorial quality level
- workflow state
