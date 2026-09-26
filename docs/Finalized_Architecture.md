# Ma'na Finalized Architecture Decisions

Version: 1.0  
Status: FROZEN  
Date: 2026-08-17

---

# Purpose

This document captures the finalized architectural decisions reached after critique and revision. It is the authoritative source for implementation. Where this document conflicts with any other document, this document wins.

---

# Specification Authority (Highest to Lowest)

1. Ma'na Vision (`docs/Architecture_Vision`)
2. Finalized Architecture Decisions (this document)
3. Ontology & Knowledge Model (`docs/04-ontology/Ontology_Knowledge_Model_v1.md`) — WRITTEN 2026-09-26, FROZEN
4. Governance Model
5. Technical Architecture
6. API Specification (`docs/10-api/ApiArchitecture_v1.md`)
7. PRD v1 — STATUS: SUPERSEDED BY SEMANTIC ONTOLOGY V2
8. Implementation tickets

---

# Layer Architecture

```
                    MA'ANA
                      │
                      ▼
             ┌─────────────────┐
             │ Ontology Layer  │
             └────────┬────────┘
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
      World         Claim         Source
        │             │              │
        └─────────────┼──────────────┘
                      ▼
             Governance Layer
                      │
            ┌─────────┴─────────┐
            ▼                   ▼
       Canonical            Proposals
        Knowledge           / Challenges
            │                   │
            └─────────┬─────────┘
                      ▼
               PostgreSQL
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
      Graph Projection       Vector Projection
        (Neo4j)               (pgvector)
           │                     │
           └──────────┬──────────┘
                      ▼
                Agent Layer
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    Relation       Architect        Gap
     Agent          Agent          Agent
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                Human Review
                      │
                      ▼
                New Knowledge
```

Cross-cutting concerns surround everything:

```
Versioning
Provenance
Audit
Evaluation
Observability
```

---

# Core Principles (Frozen)

## 1. Governed Knowledge Base is the Source of Truth

PostgreSQL is its canonical persistence layer. Neo4j is the projection of governed semantic relationships. Vector indexes are projections for semantic proximity.

The conceptual source of truth is the **governed knowledge model**.

## 2. AI Proposes, Human Approves

No AI agent may silently mutate canonical architecture. AI outputs are proposals, not facts.

Automatic: embeddings, duplicate detection, related-world suggestions, vector indexing, graph synchronization.  
Human approval required: chapter movement, chapter splitting, new semantic cluster, canonical relation, deletion, structural redesign.

## 3. Never Ingest Documents, Always Ingest Knowledge

A poem is only a source. The real product is the knowledge extracted from it.

## 4. Ontology is Language-Independent

Language is metadata. The ontology remains language independent. Adding Persian, Arabic, or English requires only: new Parser, new Tokenizer, new Vocabulary Dataset.

## 5. Scalability by Infrastructure, Not Redesign

Design for 20 million literary units. Optimize for 2,000. The architecture must never require redesign when the corpus grows.

---

# Entity Model (Frozen Decisions)

## World

A World is a semantic concept with multilingual identity. Examples: خیال (Khayal), عشق (Ishq), تصور (Tasawwur).

### Key Properties

- canonical_term, transliteration
- multilingual_glosses: {persian, urdu, arabic, english}
- short_definition, literal_meaning, expanded_meaning
- semantic_dimensions: {quranic, philosophical, literary, modern}
- central_question, central_axis
- status: DRAFT | PROPOSED | APPROVED | DEPRECATED | MERGED | SUPERSEDED
- scope: GLOBAL | TRADITION | WORKSPACE
- current_version_id, version_history[]

### Derived Properties (Never Direct-Edited)

- semantic_weight: float
- maturity: float
- centrality: float

### World Content States

A World can be canonical as an ontology object while its individual dimensions, interpretations, historical assertions, and relationships may have different evidentiary states:

```
WORLD: عشق
  Status: CANONICAL (APPROVED)

  Definition: APPROVED
  Rumi dimension: APPROVED
  Bedil dimension: PROPOSED
  Relationship عشق→فنا: CHALLENGED
  Modern interpretation: DRAFT
```

This allows representing intellectual uncertainty without making the entire World uncertain.

## LexicalForm

A lexical form is a word or phrase in a specific language.

**Not** the same as a World.

```
Word: دل
  └── participates in multiple semantic Worlds depending on context
```

Relationship:
```
LexicalForm
       ↓
Concept / World
```

## WordFamily

A linguistic grouping of related lexical forms.

**Different from OntologyRegistry.**  
A Word Family is linguistic. An Ontology Registry is conceptual. Do not mix them.

## SemanticCluster

A finer grouping within a Part. First-class graph node.

```
Chapter 9
     │
     ▼
Cluster: Imagination
     │
     ├── خیال
     ├── تصور
     ├── استعارہ
     └── تخیل
```

## Chapter / Part

Major semantic section and subdivision.

## Claim

The smallest active knowledge object in Ma'na. A Claim asserts something about a source, work, witness, unit, ontology entity, relation, or interpretation.

### Claim Structure

```
Claim
─────
claim_id
subject (entity reference)
predicate (relation type)
object (entity reference or literal)
claim_type: factual | descriptive | interpretive | comparative | historical | ontological | relational | editorial | inferential
text
status: PROPOSED | REVIEWED | APPROVED | REJECTED | CHALLENGED | SUPERSEDED
scope: GLOBAL | TRADITION | WORKSPACE
confidence: float
Evidence[]
Provenance[]
```

### Claim Atomicity

One assertion per claim. Composite claims increase review complexity and reduce auditability.

### Claim ↔ World Relationship

A World can be canonical without supporting Claims.  
Claims are assertions *about* Worlds (and other entities).

```
World: عشق
  Status: CANONICAL

  ↓ supported by
Claims: [C-00981, C-00982, C-00983]
  each with their own evidence, status, provenance
```

## Evidence

Any support, constraint, or challenge for a claim.

### Evidence Dimensions (Not Fixed Hierarchy)

- source_authority
- directness
- textual_proximity
- scholarly_reliability
- independence
- specificity
- verification_status

Calculate `evidence_strength` from these dimensions. Do not encode as a fixed numeric hierarchy because "strongest evidence" depends on the claim type.

## Source / Witness / Segment / Unit

Immutable entities as defined in Architecture_Vision.

- All units are segments. Not all segments are units.
- Unit is the main attachment point for commentary, interpretation, and ontology mapping.

## Relation

A meaning-bearing connection between two Worlds. A semantic relationship is itself a knowledge assertion.

```
عشق ──[DEEPENS_TOWARD]──► فنا
  │ supported_by → C-00981
  │ supported_by → Evidence-123
```

## SemanticPath

A first-class entity representing a meaningful journey through Worlds.

Example: Journey of the Lover: عشق → شوق → طلب → فراق → صبر → وصال → فنا → بقا

Serves simultaneously as:
- App exploration route
- Book reading route
- Podcast series
- AI Teacher curriculum

## SemanticCluster

A first-class graph node for controlling complexity at scale.

## OntologyRegistry

Maintains:
- canonical World
- aliases
- translations
- spellings
- historical forms
- language forms
- status

This is conceptual, not linguistic. Do not confuse with WordFamily.

## Contributor / Tradition / ProvenanceRecord

As defined in Architecture_Vision.

---

# Knowledge Lifecycle (Frozen)

## World Lifecycle

```
ACTIVE
DEPRECATED
MERGED
SUPERSEDED
```

## Claim Lifecycle

```
                 ┌──────────────┐
                 │   DISCOVERED  │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │   PROPOSED   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │   REVIEWED   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │   APPROVED   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │   PUBLISHED  │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │  SUPERSEDED  │
                 └──────────────┘
```

Side states:
```
PROPOSED ───────► REJECTED

APPROVED ───────► CHALLENGED
                      │
                      ▼
                  REVIEWED
                      │
             ┌────────┴────────┐
             ▼                 ▼
          APPROVED          SUPERSEDED
```

**Rejected objects remain in history. Never delete knowledge proposals simply because they were wrong. They are part of the intellectual audit trail.**

## Challenge Governance Workflow

When readers/viewers identify errors in approved knowledge, they can initiate a **Challenge**:

### Challenge Lifecycle
```
OPEN
  ↓
UNDER_REVIEW
  ↓
RESOLVED
```

### Challenge Resolutions
| Resolution | Entity Outcome | Description |
|------------|----------------|-------------|
| `REAFFIRMED` | `APPROVED` | Challenge rejected; original stands |
| `SUPERSEDED` | `SUPERSEDED` | New version created; old linked via `version_history` |
| `MERGED` | `MERGED` | Merged into another entity |
| `WITHDRAWN` | `APPROVED` | Challenger withdrew challenge |

### Challenge Flow
```
Reader creates Challenge
       ↓
Entity status → CHALLENGED (enters review queue)
       ↓
Curator reviews: original + challenge + new evidence
       ↓
Curator resolves with one of four resolutions
       ↓
Entity status updated per resolution table above
       ↓
Challenge status → RESOLVED
```

### API Endpoints
```
POST   /worlds/{id}/challenge       # Create challenge on World
GET    /worlds/{id}/challenges      # List challenges on World
POST   /claims/{id}/challenge       # Create challenge on Claim
GET    /claims/{id}/challenges      # List challenges on Claim
POST   /relations/{id}/challenge    # Create challenge on Relation
GET    /relations/{id}/challenges   # List challenges on Relation
POST   /challenges/{id}/resolve     # Resolve challenge (curator only)
```

### Versioning on SUPERSEDED
When a challenge is resolved as `SUPERSEDED`:
1. Curator creates new World/Claim/Relation version
2. Original entity marked `SUPERSEDED`
3. `version_history` on original updated with new entity ID
4. Graph/vector projections updated to point to new version
5. Old version remains in history (audit trail preserved)
```

## Embedding Lifecycle

```
DRAFT
PROPOSED
APPROVED        ← only this enters default retrieval index
SUPERSEDED
REJECTED
```

---

# Graph Architecture (Frozen)

## Dual Graph Design

```
                 Neo4j
              /         \
             /           \
     Canonical Graph    Proposal Graph
           │                  │
       APPROVED          PROPOSED / CHALLENGED
```

This lets the Architect Agent reason about proposed architecture without contaminating canonical knowledge.

## Claim-Supported Relations

Instead of bare graph edges:

```
عشق ──[RELATES_TO]──► فنا
```

We have:

```
عشق
  │
  └── DEEPENS_TOWARD
           │
           ▼
          فنا
          
  supported_by → C-00981
  supported_by → Evidence-123
```

A semantic relationship is a **governed knowledge assertion**.

---

# Vector Architecture (Frozen)

## Initial Phase: PostgreSQL + pgvector

Start with pgvector. Later, if scale demands it, migrate to Qdrant.

## VectorStore Abstraction (Required from Day 1)

```python
class VectorStore:
    upsert(embeddings)
    query(vector, filters, limit, embedding_type, model_version, scope)
    delete(entity_id)
    reindex(from_model, to_model)
    health_check()
    get_by_entity(entity_id)
    count()
    get_model_info()
```

Application code depends only on this interface. Migration from pgvector to Qdrant does not change the domain model.

## Embedding Types (Per Entity)

```
World embeddings: world_full, world_definition, world_meaning, world_literary, world_philosophical, world_modern, world_questions
Claim embeddings: claim_text, claim_evidence
Source embeddings: source_segment, source_translation
```

They should not live in an undifferentiated vector pool.

## Embedding Provenance

Every embedding must record:
- embedding_id
- entity_id, entity_type
- embedding_type
- model, model_version, dimensions
- source_version, content_hash
- created_at

This enables regeneration when models change.

## Embedding Eligibility

Only APPROVED entities enter the default retrieval index.

---

# World Merge Protocol (Frozen)

When Worlds may be synonyms or near-synonyms (e.g., شوق and اشتیاق):

1. Agent proposes MERGE
2. System collects Claims from both Worlds
3. Conflict detection runs
4. Human review
5. Canonical World produced

**Nothing disappears.** Old IDs become aliases/redirects:

```
W4871 ──[MERGED_INTO]──► W3012
```

At 10,000+ Worlds, this becomes critical.

---

# Scope Model (Frozen for Design)

```
scope: GLOBAL | TRADITION | WORKSPACE
```

**Phase 0:** All entities are GLOBAL. Schema must support expansion.

**Deferred:** Full multi-tenant architecture. Do not build collaborative SaaS features in Phase 0.

---

# API Architecture (Frozen Additions)

Add to `ApiArchitecture_v1.md`:

## Batch Operations

```
POST /claims/batch-review
POST /worlds/batch-review
```

## History Endpoints

```
GET /worlds/{id}/history
GET /claims/{id}/history
```

## Global Search

```
GET /search?q=...
```

Spans claims, worlds, commentaries, sources.

## Idempotency (Enforced, Not Just Documented)

```
Idempotency-Key
       ↓
  request hash
       ↓
  stored result
       ↓
  repeat request
       ↓
  same result
```

---

# Agent Architecture (Frozen)

## Architect Agent

Produces proposals, not rankings:

```json
{
  "proposal_type": "RESTRUCTURE",
  "reason": "...",
  "evidence": [],
  "affected_worlds": [],
  "current_architecture": {},
  "proposed_architecture": {},
  "confidence": 0.86
}
```

Curator sees:
```
CURRENT: A → B → C → D
PROPOSED: A → B → X → C → D
WHY: ...
EVIDENCE: ...
IMPACT: ...
```

## Ring / Architecture Evaluation Dimensions

Not a single score. Multi-dimensional:

```
semantic_coherence
transition_quality
central_question_alignment
redundancy
coverage
closure
asymmetry_justification
```

Then optionally:
```
overall_architectural_confidence
```

**Symmetry is an optional architectural property, not an optimization target. Semantic coherence takes precedence over structural symmetry.**

## Agent Evaluation (Required)

Three test types:

### Deterministic Tests
Database, API, graph projection correctness.

### Semantic Evaluation
Relation Agent tested on known pairs:
```
خیال ↔ تصور → strong semantic relation
خیال ↔ جمود → semantic contrast
خیال ↔ اقتصاد → irrelevant
```

### Architectural Evaluation
Architect Agent tested on known Chapter+World sets.

These become regression tests. Changing the LLM/model later must not silently degrade performance.

---

# Ingestion Philosophy (Reaffirmed)

```
Lecture
 ↓
Transcript
 ↓
Candidate claims
 ↓
Candidate Worlds
 ↓
Candidate relations
 ↓
Governance
 ↓
Canonical knowledge
```

Ingestion produces candidates. Governance produces canonicals.

## Multi-Stage Extraction

Never ask one LLM to do everything.

1. Parser (deterministic)
2. Entity Extraction
3. Vocabulary Extraction
4. Theme Classification
5. Human Experience Classification
6. Symbol Extraction
7. Concept Extraction
8. Commentary Generation
9. Human Review

Each stage produces structured JSON.

---

# Retrieval Architecture (Reaffirmed)

## Retrieval Layers

1. Source Retrieval — original text, witness comparison
2. Commentary Retrieval — unit commentary, question-centered commentary
3. Claim Retrieval — approved claims, contested interpretations
4. Ontology Retrieval — works linked to experience, uses of a symbol
5. Graph Retrieval — concept-to-concept through governed relations
6. Semantic Retrieval — passages similar to feeling or question

## Query Modes

1. Source-Seeking
2. Explanation-Seeking
3. Concept-Seeking
4. Question-Seeking
5. Disagreement-Seeking (competing interpretations, not flattened answer)
6. Comparative

Retrieval should combine layers, not rely on one.

---

# Testing Strategy (Frozen)

## Three Test Types

1. **Deterministic:** DB, API, graph projection, migration correctness
2. **Semantic:** Agent output quality on known pairs
3. **Architectural:** Chapter evaluation on known structures

All become regression tests.

---

# What Is Explicitly Deferred

- Offline curation
- XML/RDF content negotiation
- Full multi-tenancy (design now, implement later)
- Distributed tracing (basic structured logs first)
- Qdrant migration machinery (create VectorStore abstraction; build migration only when needed)
- Massive literary corpus ingestion (first make the World engine reliable)

---

# Implementation Roadmap (Revised)

## Days 1–2: Ontology & Knowledge Model v1

Define:
- World, LexicalForm, WordFamily, SemanticCluster, Chapter, Part
- Claim, Evidence, Source, Relation, SemanticPath, Scope, Version, Proposal

## Days 3–4: Vertical Slice #1

Implement one complete World lifecycle using **خیال**:

```
Create World → Validate → Store → Version → Claim → Evidence → Approve → Embed → Graph → Search
```

Stack: PostgreSQL + basic CRUD API

## Day 5: Vector Slice

```
World → embedding → pgvector → semantic search
```

With VectorStore abstraction.

## Day 6: Graph Slice

```
World → Relation → Neo4j projection → graph traversal
```

## Day 7: Vertical Slice #2

Add **تصور** and verify **خیال → تصور** works across Postgres, Graph, Vector, Governance.

## Days 8–9: Relation Agent

```
New World → candidates → relation proposals → evidence → review
```

## Day 10: Architect Agent

Proposals only. No automatic mutation.

## Day 11: Ring / Architecture Agent

Evaluate coherence, central question, transitions, redundancy, closure, justified asymmetry.

## Day 12: Gap + Merge Agent

Test: missing World, duplicate World, near-synonym, merge, split.

## Days 13–14: Evaluation + Architecture Review

Regression suite. Production test with **خیال + تصور + استعارہ**.

**Validation criterion:** The system ingests these three Worlds and correctly proposes **خیال → تصور → استعارہ** while preserving evidence, versions, graph relationships, embeddings, and human approval.

---

# Next Document

**`Ma'ana Ontology & Knowledge Model v1.0`** — WRITTEN, FROZEN.
See `docs/04-ontology/Ontology_Knowledge_Model_v1.md`.

This document must formally define:
- Every entity, its fields, enums, and types
- Relationship types and cardinalities
- Invariants
- Lifecycle state machines
- World/Claim semantics
- Versioning rules
- Merge/split rules
- Scope rules
- Exact mapping to PostgreSQL tables and Neo4j node/relationship types

This must be implementation-grade, not philosophical.

Once frozen, implementation can proceed without the coding agent inferring the ontology while building it.

---

# Final Verdict

The architecture is **finalized at the design level**. No further architectural revisions are needed before writing the Ontology & Knowledge Model.

The system is now specified well enough to implement reliably.
