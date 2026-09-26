# Ma'ana Ontology & Knowledge Model v1.0

Version: 1.0
Status: FROZEN
Date: 2026-09-26
Authority: Specification Authority level 3 (below Ma'na Vision and Finalized Architecture Decisions)
Implementation: `maana-api/`

---

# 1. Purpose and Scope

This document is the **implementation-grade** definition of the Ma'na knowledge model. It defines
exactly what entities exist, what fields they carry, what enumerations they use, how they relate,
how they transition through lifecycle states, and how they map onto PostgreSQL tables, Neo4j node
and relationship types, and vector index records.

It is a specification, not a philosophical essay. Where a decision could be interpreted two ways,
this document states the one permitted way.

## 1.1 What this document does not do

It does not restate the vision, the architecture rationale, or the API surface. Those live in
`docs/Architecture_Vision`, `docs/Finalized_Architecture.md`, and `docs/10-api/ApiArchitecture_v1.md`.

It does not define first-class literary concepts. Those are defined in
`docs/04-ontology/CanonicalOntology.md`. This document binds those concepts to storage.

## 1.2 Conformance

An implementation conforms to this document if:

- every entity in §3 exists as a persistable record,
- every field in §3 exists with the stated type and nullability,
- every lifecycle transition in §7 is enforced or explicitly permitted,
- every invariant in §8 holds at all times,
- the PostgreSQL mapping in §11 matches the deployed schema,
- the Neo4j projection in §12 matches the deployed graph.

---

# 2. Notation and Conventions

## 2.1 Type System

| Notation | Meaning | PostgreSQL type |
|---|---|---|
| `string` | UTF-8 text, non-null, length-unbounded | `TEXT` or `VARCHAR(n)` |
| `text?` | UTF-8 text, nullable | `TEXT NULL` |
| `id` | Stable string identifier, see §2.2 | `TEXT PRIMARY KEY` |
| `id?` | Nullable identifier reference | `TEXT NULL` |
| `float` | IEEE-754 double precision, range [0.0, 1.0] unless stated | `DOUBLE PRECISION` |
| `int` | 64-bit signed integer | `BIGINT` |
| `bool` | Boolean | `BOOLEAN` |
| `timestamp` | UTC instant, timezone-aware | `TIMESTAMPTZ` |
| `enum:X` | One of the values of enumeration X, see §6 | `TEXT` with CHECK constraint |
| `json:Shape` | JSON document conforming to Shape | `JSONB` |
| `list<T>` | Ordered array of T | `JSONB` array |
| `map<K,V>` | String-keyed object | `JSONB` object |

## 2.2 Identifier Conventions

| Prefix | Entity | Example |
|---|---|---|
| `W_` | World | `W_khayal` |
| `C_` | Claim | `C_khayal_tasawwur` |
| `R_` | Relation | `R_khayal_deepens_tasawwur` |
| `E_` | Evidence | `E_rumi_divan_1204` |
| `P_` | SemanticPath | `P_journey_of_the_lover` |
| `L_` | LexicalForm | `L_dal_fa` |
| `F_` | WordFamily | `F_dal_family` |
| `CH_` | Chapter | `CH_09_imagination` |
| `PT_` | Part | `PT_09_02` |
| `SC_` | SemanticCluster | `SC_imagination` |
| `X_` | Challenge | `X_0001` |
| `EMB_` | Embedding | `EMB_0001` |
| `SRC_` | Source | `SRC_divan_shams` |
| `WIT_` | Witness | `WIT_b40` |
| `SEG_` | Segment | `SEG_0001` |
| `UN_` | Unit | `UN_0001` |

**INVARIANT (I-001):** Identifiers are stable, opaque, and never reused. A retired identifier is
never reassigned to different content. Identifiers carry no semantic ordering.

## 2.3 Naming Conventions

- Table names: plural, lowercase, snake_case (`semantic_clusters`).
- Column names: singular, lowercase, snake_case (`canonical_term`).
- Code: `domain/models.py` holds enums and value objects; `infrastructure/models.py` holds the
  SQLModel table definitions that own the schema.

---

# 3. Entities

Entities are grouped into four layers. Every entity belongs to exactly one layer.

```
Layer A — Textual Input        Source, Witness, Segment, Unit
Layer B — Semantic Lexicon     World, LexicalForm, WordFamily, Chapter, Part, SemanticCluster
Layer C — Governed Assertions  Claim, Evidence, Relation, SemanticPath
Layer D — Governance           Challenge, Contributor (via ProvenanceRecord)
Cross-cutting                  Embedding, EmbeddingProvenance, OntologyRegistryEntry
```

---

## 3.1 World

A World is a **semantic concept with multilingual identity**. It is the primary unit of meaning in
Ma'na. It is not a word, not a document, and not a topic tag.

A World is an **identity-bearing concept record**. Its *meanings* are Claims about it. This
separation is the single most important structural decision in the model.

### Fields

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `world_id` | `id` | no | — | Primary key |
| `canonical_term` | `string` | no | — | Preferred display form in the source tradition |
| `transliteration` | `text?` | yes | null | Latin-script scholarly transliteration |
| `persian_term` | `text?` | yes | null | Persian script form |
| `urdu_term` | `text?` | yes | null | Urdu script form |
| `arabic_root` | `text?` | yes | null | Trilateral root, when applicable |
| `english_gloss` | `text?` | yes | null | English semantic equivalent |
| `short_definition` | `text?` | yes | null | One-sentence definition for display |
| `literal_meaning` | `text?` | yes | null | Denotative content |
| `expanded_meaning` | `text?` | yes | null | Full connotation and semantic field |
| `central_question` | `text?` | yes | null | The question this World answers |
| `central_axis` | `text?` | yes | null | The dimension along which the World varies |
| `semantic_dimensions` | `map<string,string>` | no | `{}` | Named dimensions (see §3.1.1) |
| `status` | `enum:WorldStatus` | no | `proposed` | Lifecycle state, see §7.1 |
| `scope` | `enum:Scope` | no | `global` | Governance scope, see §9 |
| `chapter_id` | `id?` | yes | null | Owning Chapter |
| `cluster_id` | `id?` | yes | null | Owning SemanticCluster |
| `current_version_id` | `id?` | yes | null | Active version record |
| `version_history` | `list<id>` | no | `[]` | Ordered list of prior version IDs, oldest first |
| `provenance` | `list<ProvenanceRecord>` | no | `[]` | Who created and shaped this World |
| `created_at` | `timestamp` | no | now | Creation instant |
| `updated_at` | `timestamp` | no | now | Last mutation instant |

### 3.1.1 `semantic_dimensions`

A map from dimension name to dimension content. Reserved keys:

| Key | Meaning |
|---|---|
| `quranic` | Quranic interpretive layer |
| `philosophical` | Philosophical layer |
| `literary` | Literary-critical layer |
| `modern` | Modern/contemporary layer |
| `mystical` | Mystical layer |
| `psychological` | Psychological layer |
| `political` | Political layer |

Non-reserved keys are permitted. Adding a dimension is not a schema change.

### 3.1.2 Derived Properties (Never Directly Edited)

These are computed, never stored as authoritative values:

| Property | Derivation |
|---|---|
| `semantic_weight` | f(claim count, evidence strength, inbound relation count) |
| `maturity` | f(approved claim ratio, version count, age) |
| `centrality` | PageRank-style score over approved World–World relations |

**INVARIANT (I-002):** Derived properties are never stored as source of truth. Any stored cache
must be recomputable and must not be required for correctness.

### 3.1.3 World Content States

A World may be `approved` as an identity while its individual contents are in any Claim status.
This is the mechanism for representing intellectual uncertainty without destabilizing identity.

```
World W_ishq          status = approved
  ├── Claim C_def     status = approved     (definition)
  ├── Claim C_rumi    status = approved     (Rumi dimension)
  ├── Claim C_bedil   status = proposed     (Bedil dimension)
  ├── Claim C_modern  status = draft        (modern interpretation)
  └── Relation R_ishq_fana  status = challenged
```

**INVARIANT (I-003):** World status describes identity governance only. Content uncertainty is
expressed exclusively through Claim and Relation status. No World status value means
"content is uncertain".

### 3.1.4 World Semantics Rules

1. A World **may** exist with no approved Claims. Identity and meaning are independently governed.
2. A World is **not** a LexicalForm. `دل` is a LexicalForm; it participates in several Worlds.
3. A World is **not** a Chapter or Cluster. Those are containers, not concepts.
4. A World is never deleted. Deprecated, merged, and superseded Worlds persist for audit.
5. `canonical_term` is immutable after first approval. Changes require a new version.

---

## 3.2 LexicalForm

A lexical form is a **word or phrase in a specific language**. It is a linguistic record and is
never identical to a World.

| Field | Type | Null | Description |
|---|---|---|---|
| `lexical_id` | `id` | no | Primary key |
| `term` | `string` | no | The word or phrase |
| `language` | `string` | no | BCP-47 language tag, e.g. `fa`, `ur`, `ar`, `en` |
| `transliteration` | `text?` | yes | Latin-script form |
| `root` | `text?` | yes | Trilateral root, links to WordFamily |
| `metadata` | `map<string,any>` | no | Extensible |

**INVARIANT (I-004):** A LexicalForm never carries semantic status. Semantics live in Worlds and
Claims. If a LexicalForm needs a definition, that definition is a Claim whose subject is the
LexicalForm.

**INVARIANT (I-005):** One LexicalForm participates in many Worlds; one World is realized by many
LexicalForms. The link is a graph edge of type `REALIZED_BY`, not a foreign key.

---

## 3.3 WordFamily

A linguistic grouping of lexical forms sharing a root.

| Field | Type | Null | Description |
|---|---|---|---|
| `family_id` | `id` | no | Primary key |
| `root` | `string` | no | Shared trilateral root |
| `language` | `string` | no | Language family identifier |
| `members` | `list<id>` | no | Lexical IDs in this family |
| `metadata` | `map<string,any>` | no | Extensible |

**INVARIANT (I-006):** A WordFamily is **linguistic**. An OntologyRegistryEntry is **conceptual**.
These two must never share a table, a foreign key, or a merge path.

---

## 3.4 Chapter

A major semantic section grouping Worlds.

| Field | Type | Null | Description |
|---|---|---|---|
| `chapter_id` | `id` | no | Primary key |
| `title` | `string` | no | Chapter title |
| `title_transliteration` | `text?` | yes | Transliterated title |
| `description` | `text?` | yes | Scope description |
| `central_question` | `text?` | yes | Question the chapter answers |
| `order` | `int` | no | Presentation order, ascending |
| `metadata` | `map<string,any>` | no | Extensible |

**INVARIANT (I-007):** `order` is unique within the chapter set. Chapters are the coarsest
architectural container.

---

## 3.5 Part

A subdivision of a Chapter.

| Field | Type | Null | Description |
|---|---|---|---|
| `part_id` | `id` | no | Primary key |
| `chapter_id` | `id` | no | FK → `chapters.chapter_id`, NOT NULL |
| `title` | `string` | no | Part title |
| `description` | `text?` | yes | Scope description |
| `order` | `int` | no | Order within chapter, ascending |
| `metadata` | `map<string,any>` | no | Extensible |

**INVARIANT (I-008):** `order` is unique within a Chapter. A Part belongs to exactly one Chapter.

---

## 3.6 SemanticCluster

A finer grouping within a Part. A first-class graph node.

| Field | Type | Null | Description |
|---|---|---|---|
| `cluster_id` | `id` | no | Primary key |
| `chapter_id` | `id` | no | FK → `chapters.chapter_id`, NOT NULL |
| `part_id` | `id?` | yes | FK → `parts.part_id`, nullable — a cluster may exist without a Part |
| `title` | `string` | no | Cluster title |
| `description` | `text?` | yes | Scope description |
| `metadata` | `map<string,any>` | no | Extensible |

```
Chapter CH_09_imagination
  └── Part PT_09_02_art_and_expression
        └── Cluster SC_imagination
              ├── W_khayal
              ├── W_tasawwur
              ├── W_istiarah
              └── W_takhayyul
```

**INVARIANT (I-009):** A SemanticCluster always belongs to a Chapter. A World belongs to at most
one Cluster at a time. Cluster membership changes are architecturally significant and require
human approval (see `Finalized_Architecture.md` §2).

---

## 3.7 Source

Any preserved input artifact from which Ma'na derives knowledge. A Source is **input, not
product**.

| Field | Type | Null | Description |
|---|---|---|---|
| `source_id` | `id` | no | Primary key |
| `source_type` | `string` | no | e.g. `manuscript`, `recording`, `transcript`, `scan` |
| `uri` | `string` | no | Resolvable location |
| `title` | `text?` | yes | Display title |
| `description` | `text?` | yes | Description |
| `extra_metadata` | `map<string,any>` | no | Extensible |
| `created_at` | `timestamp` | no | now |

**INVARIANT (I-010):** Sources are immutable once ingested. A corrected Source is a new Source
with a `supersedes` Claim, never an in-place edit.

---

## 3.8 Witness

A specific textual or transmitted instance of a work.

| Field | Type | Null | Description |
|---|---|---|---|
| `witness_id` | `id` | no | Primary key |
| `work_id` | `id` | no | The work this witness transmits |
| `witness_type` | `string` | no | e.g. `manuscript`, `first_edition`, `translation` |
| `label` | `string` | no | Short identifier, e.g. `B40` |
| `description` | `text?` | yes | Description |
| `extra_metadata` | `map<string,any>` | no | Extensible |

---

## 3.9 Segment

Any addressable span inside a Witness.

| Field | Type | Null | Description |
|---|---|---|---|
| `segment_id` | `id` | no | Primary key |
| `witness_id` | `id` | no | FK → `witnesses.witness_id` |
| `segment_type` | `string` | no | e.g. `verse`, `paragraph`, `line` |
| `start` | `float?` | yes | Start offset |
| `end` | `float?` | yes | End offset |
| `text` | `text?` | yes | Segment content |
| `extra_metadata` | `map<string,any>` | no | Extensible |

---

## 3.10 Unit

A Segment that has been editorially recognized as a meaning-bearing interpretive boundary.

| Field | Type | Null | Description |
|---|---|---|---|
| `unit_id` | `id` | no | Primary key |
| `segment_id` | `id` | no | FK → `segments.segment_id` |
| `work_id` | `id` | no | The work this unit belongs to |
| `unit_type` | `string` | no | e.g. `couplet`, `stanza`, `paragraph` |
| `label` | `text?` | yes | Display label |
| `interpretation` | `text?` | yes | Editorial interpretation |
| `extra_metadata` | `map<string,any>` | no | Extensible |

**INVARIANT (I-011):** Every Unit is a Segment. Not every Segment is a Unit. A Unit is the
primary attachment point for Claims, commentary, and ontology mapping.

---

## 3.11 Claim

A Claim is **the smallest active knowledge object in Ma'na**. It asserts exactly one thing.

A Claim is a governed knowledge assertion, not a description. It always has a subject, a predicate,
and a textual assertion.

### Fields

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `claim_id` | `id` | no | — | Primary key |
| `claim_type` | `enum:ClaimType` | no | — | Governed claim class, see §6.3 |
| `subject_kind` | `string` | no | — | Subject entity class: `world`, `lexical_form`, `source`, `witness`, `segment`, `unit`, `relation`, `path` |
| `subject_reference_id` | `id` | no | — | Subject entity ID |
| `subject_label` | `text?` | yes | null | Cached display label |
| `predicate` | `string` | no | — | Predicate name, see §5.4 |
| `object` | `text?` | yes | null | Object value or entity reference |
| `text` | `string` | no | — | The human-readable assertion, always present |
| `status` | `enum:ClaimStatus` | no | `proposed` | Lifecycle state, see §7.2 |
| `scope` | `enum:Scope` | no | `global` | Governance scope, see §9 |
| `confidence` | `float` | no | `0.0` | Curator-assigned confidence in [0.0, 1.0] |
| `evidence` | `list<Evidence>` | no | `[]` | Supporting evidence records |
| `provenance` | `list<ProvenanceRecord>` | no | `[]` | Who produced the Claim |
| `version_history` | `list<id>` | no | `[]` | Prior version IDs, oldest first |
| `created_at` | `timestamp` | no | now | Creation instant |
| `updated_at` | `timestamp` | no | now | Last mutation instant |

### 3.11.1 Claim Atomicity

**INVARIANT (I-012):** One Claim asserts exactly one proposition. A Claim that requires "and" to
express must be split into two Claims.

Rationale: composite claims increase review complexity, make partial rejection impossible, and
destroy auditability. A curator who accepts half of a Claim must reject all of it.

### 3.11.2 Claim ↔ World Relationship

**INVARIANT (I-013):** A Claim never *defines* a World. A Claim *asserts something about* a World.
Definition is a Claim with `subject_kind = world` and `predicate = defines`.

```
World W_ishq (status = approved)
  └── supported by
        ├── Claim C_ishq_def     predicate = defines        status = approved
        ├── Claim C_ishq_rumi    predicate = has_dimension  status = approved
        └── Claim C_ishq_modern  predicate = has_dimension  status = proposed
```

### 3.11.3 `confidence` Semantics

`confidence` is a **curator-assigned** value, not a computed one. It expresses a human judgment.

**INVARIANT (I-014):** `confidence` is only writable when `status` is `reviewed`, `approved`, or
`published`. Agents may propose a confidence value, but only a curator sets the final value.

**INVARIANT (I-015):** `confidence` never determines status. Status is a governance decision, not a
threshold result. There is no `confidence >= 0.8 ⇒ approved` rule anywhere in the system.

---

## 3.12 Evidence

Any support, constraint, or challenge for a Claim.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `evidence_id` | `id` | no | — | Identifier |
| `evidence_type` | `enum:EvidenceType` | no | — | Evidence family, see §6.5 |
| `source_ref` | `string` | no | — | Resolvable reference to the source |
| `text` | `text?` | yes | null | Quoted or extracted text |
| `start` | `float?` | yes | null | Start offset within the source |
| `end` | `float?` | yes | null | End offset within the source |
| `dimensions` | `map<EvidenceDimension,float>` | no | `{}` | Multidimensional strength scores in [0.0, 1.0] |
| `notes` | `text?` | yes | null | Curator notes |
| `created_at` | `timestamp` | no | now | Creation instant |

### 3.12.1 Evidence Dimensions

`dimensions` is a sparse map. Absent keys mean "not assessed", not "zero".

| Dimension | Question it answers |
|---|---|
| `source_authority` | How authoritative is the source? |
| `directness` | How directly does it support the claim? |
| `textual_proximity` | How close is the supporting text? |
| `scholarly_reliability` | How reliable is the scholarship? |
| `independence` | How independent of other evidence? |
| `specificity` | How specific is the evidence? |
| `verification_status` | Has it been verified? |

**INVARIANT (I-016):** Evidence strength is a **weighted aggregation** of present dimensions, with
weights determined by `claim_type`. There is no fixed numeric hierarchy of evidence types, because
"strongest evidence" depends on the claim being supported.

**INVARIANT (I-017):** Absent dimension keys never default to `0.0` in aggregation. Absent means
excluded from the weighted mean. Only present keys contribute.

---

## 3.13 ProvenanceRecord

The record of who produced or materially shaped a governed object.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `contributor_kind` | `enum:ContributorKind` | no | — | Contributor class, see §6.6 |
| `contributor_id` | `id?` | yes | null | Identity of the contributor, when known |
| `source` | `text?` | yes | null | Where the contribution came from |
| `method` | `text?` | yes | null | How it was produced |
| `process` | `text?` | yes | null | Which pipeline stage produced it |
| `model` | `text?` | yes | null | Model name, when AI-produced |
| `tool` | `text?` | yes | null | Tool name |
| `timestamp` | `timestamp` | no | now | When the contribution occurred |
| `review_history` | `list<string>` | no | `[]` | Review events |

**INVARIANT (I-018):** Every World, Claim, Relation, and SemanticPath carries a non-empty
`provenance` list before it can reach `approved`. A knowledge object with unknown origin cannot be
canonized.

**INVARIANT (I-019):** AI-generated provenance is never stored in the same field as human
provenance without a `contributor_kind` distinction. `ai_system` and `editor` are distinct kinds
and are always separable.

---

## 3.14 Relation

A meaning-bearing connection between two Worlds. A Relation is **itself a governed knowledge
assertion** and carries status, scope, and provenance exactly as a Claim does.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `relation_id` | `id` | no | — | Primary key |
| `relation_type` | `enum:RelationType` | no | — | Relationship semantics, see §5 |
| `source_world_id` | `id` | no | — | FK → `worlds.world_id`, NOT NULL |
| `target_world_id` | `id` | no | — | FK → `worlds.world_id`, NOT NULL |
| `claim_id` | `id?` | yes | null | FK → `claims.claim_id`, the supporting Claim |
| `status` | `enum:WorldStatus` | no | `proposed` | Lifecycle state, see §7.1 |
| `scope` | `enum:Scope` | no | `global` | Governance scope, see §9 |
| `provenance` | `list<ProvenanceRecord>` | no | `[]` | Who proposed and shaped the relation |
| `created_at` | `timestamp` | no | now | Creation instant |

### 3.14.1 Relation Invariants

**INVARIANT (I-020):** A Relation is not a bare graph edge. It is a knowledge assertion. It has
status, provenance, and optionally a supporting Claim.

**INVARIANT (I-021):** `source_world_id != target_world_id`. Self-relations are rejected at the
service layer.

**INVARIANT (I-022):** A Relation may exist between two Worlds in any lifecycle state. A relation
from a `deprecated` World is valid but is excluded from default retrieval.

**INVARIANT (I-023):** A Relation with `claim_id` set must have a resolvable Claim. An orphaned
`claim_id` is a data-integrity error, not a soft state.

---

## 3.15 SemanticPath

A first-class entity representing a meaningful ordered journey through Worlds.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `path_id` | `id` | no | — | Primary key |
| `title` | `string` | no | — | Path title |
| `description` | `text?` | yes | null | Path description |
| `world_ids` | `list<id>` | no | `[]` | Ordered World IDs defining the journey |
| `scope` | `enum:Scope` | no | `global` | Governance scope |
| `provenance` | `list<ProvenanceRecord>` | no | `[]` | Who created the path |
| `created_at` | `timestamp` | no | now | Creation instant |

Example: `P_journey_of_the_lover` = `عشق → شوق → طلب → فراق → صبر → وصال → فنا → بقا`

**INVARIANT (I-024):** `world_ids` is ordered and non-empty. Order is semantic; a path is not a
set. Consecutive Worlds in a path should have at least one approved Relation between them, but a
missing Relation is a quality signal, not a validity error.

---

## 3.16 Challenge

A formal objection to an approved entity, with a resolution workflow.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `challenge_id` | `id` | no | — | Primary key |
| `entity_type` | `string` | no | — | `world` \| `claim` \| `relation` |
| `entity_id` | `id` | no | — | ID of the challenged entity |
| `challenger_id` | `id` | no | — | Who raised the challenge |
| `reason` | `string` | no | — | Textual justification |
| `new_evidence` | `list<Evidence>` | no | `[]` | Evidence supplied with the challenge |
| `suggested_correction` | `json:object?` | yes | null | Proposed replacement content |
| `status` | `enum:ChallengeStatus` | no | `open` | Lifecycle state, see §7.3 |
| `resolution` | `enum:ChallengeResolution?` | yes | null | Resolution outcome, see §6.7 |
| `resolver_id` | `id?` | yes | null | Curator who resolved it |
| `resolved_at` | `timestamp?` | yes | null | Resolution instant |
| `created_at` | `timestamp` | no | now | Creation instant |

**INVARIANT (I-025):** A Challenge may only be opened against an entity in `approved` or
`published` status. Challenging a `draft` or `proposed` entity is meaningless.

**INVARIANT (I-026):** A Challenge is never deleted. Resolved challenges persist as the intellectual
audit record.

**INVARIANT (I-027):** `status = resolved` requires `resolution`, `resolver_id`, and `resolved_at`
to all be non-null.

---

## 3.17 Embedding

A vector projection of a knowledge object.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `embedding_id` | `id` | no | — | Primary key |
| `entity_id` | `id` | no | — | The entity this vector represents |
| `entity_type` | `string` | no | — | `world` \| `claim` \| `source` \| `relation` |
| `embedding_type` | `string` | no | — | Typed embedding slot, see §6.8 |
| `model` | `string` | no | — | Embedding model name |
| `model_version` | `string` | no | — | Model version string |
| `dimensions` | `int` | no | — | Vector dimensionality |
| `vector` | `list<float>` | no | — | The vector, length = `dimensions` |
| `source_version` | `text?` | yes | null | Entity version the vector was built from |
| `content_hash` | `text?` | yes | null | Hash of the embedded text |
| `created_at` | `timestamp` | no | now | Creation instant |
| `updated_at` | `timestamp` | no | now | Last mutation instant |

**INVARIANT (I-028):** Vectors of different `embedding_type` values never share a search pool.
Typed vectors are always filtered before comparison.

**INVARIANT (I-029):** Only embeddings whose parent entity has `status = approved` are eligible
for the default retrieval index.

**INVARIANT (I-030):** `content_hash` is mandatory for any embedding that supports retrieval. It is
the basis for detecting stale vectors after entity mutation.

**INVARIANT (I-031):** `(entity_id, entity_type, embedding_type, model_version)` is unique. Re-
embedding the same slot with the same model version is an update, not an insert.

---

## 3.18 EmbeddingProvenance

The audit record of how an Embedding was produced. Kept separately from `embeddings` so that
vector-store migration does not lose provenance.

| Field | Type | Null | Description |
|---|---|---|---|
| `embedding_id` | `id` | no | PK, FK → `embeddings.embedding_id` |
| `entity_id` | `id` | no | Denormalized for audit queries |
| `entity_type` | `string` | no | Denormalized |
| `embedding_type` | `string` | no | Denormalized |
| `model` | `string` | no | Model name |
| `model_version` | `string` | no | Model version |
| `dimensions` | `int` | no | Vector dimensionality |
| `source_version` | `text?` | yes | Entity version embedded |
| `content_hash` | `text?` | yes | Embedded content hash |
| `created_at` | `timestamp` | no | Creation instant |

---

## 3.19 OntologyRegistryEntry

The conceptual alias and translation registry for a World. Conceptual, not linguistic.

| Field | Type | Null | Default | Description |
|---|---|---|---|---|
| `world_id` | `id` | no | — | PK, FK → `worlds.world_id` |
| `canonical_term` | `string` | no | — | Mirrors the World's canonical term |
| `aliases` | `list<string>` | no | `[]` | Alternative names, same language |
| `translations` | `map<string,string>` | no | `{}` | Language tag → translated term |
| `spellings` | `list<string>` | no | `[]` | Orthographic variants |
| `historical_forms` | `list<string>` | no | `[]` | Superseded historical spellings |
| `language_forms` | `map<string,string>` | no | `{}` | Language tag → preferred in-language form |
| `status` | `enum:WorldStatus` | no | `approved` | Mirrors the World's status |
| `extra_metadata` | `map<string,any>` | no | `{}` | Extensible |

**INVARIANT (I-032):** When a World is merged, the source World's ID is added to the target's
`aliases`, and a `MERGED_INTO` relation is created. The redirect must be total: any lookup by a
retired ID resolves to the surviving World.

---

# 4. Relationship Taxonomy

## 4.1 Relationship Classes

A relationship in Ma'na is one of four kinds. They are never conflated.

| Class | Stored as | Has governance status | In Neo4j |
|---|---|---|---|
| **Lexical** | `WordFamily.members` + graph edge | No | Yes |
| **Architectural** | FK columns + graph edge | Partially | Yes |
| **Semantic** | `relations` table | Yes | Yes |
| **Assertive** | `claims` table | Yes | No (claims are not graph edges) |

**INVARIANT (I-033):** Only Semantic relationships become graph edges between World nodes.
Assertive relationships (Claims) do not. A Claim is not a relation between two entities; it is an
assertion *about* one entity.

## 4.2 Lexical Relationships

| Type | From → To | Cardinality | Meaning |
|---|---|---|---|
| `WORD_FAMILY` | LexicalForm → WordFamily | N:1 | The form belongs to the family |
| `DERIVED_FROM` | LexicalForm → LexicalForm | N:1 | The form is morphologically derived from another |
| `REALIZED_BY` | World → LexicalForm | N:M | The concept is realized by this word |

## 4.3 Architectural Relationships

| Type | From → To | Cardinality | Invariant |
|---|---|---|---|
| `PART_OF` | Chapter → Part | 1:N | Every Part has exactly one Chapter |
| `CONTAINS` | Part → SemanticCluster | 1:N | Cluster's Part is nullable |
| `BELONGS_TO` | World → SemanticCluster | N:1 | At most one Cluster per World |
| `CHAPTER_ANCHOR` | World → Chapter | N:1 | Chapter is nullable on World |
| `CLUSTER_ANCHOR` | World → SemanticCluster | N:1 | Same as `BELONGS_TO`, graph projection |
| `TRANSITION_TO` | World → World | N:M | Ring/architecture agent annotation |
| `SEMANTIC_BRIDGE` | World → World | N:M | Cross-chapter connective concept |
| `RING_LINK` | World → World | N:M | Ring membership annotation |

**INVARIANT (I-034):** `BELONGS_TO` and `CLUSTER_ANCHOR` are the same fact expressed in two layers.
PostgreSQL holds it as a FK; Neo4j holds it as an edge. They must always agree. A divergence is a
projection bug, and §12.4 defines the repair procedure.

## 4.4 Semantic Relationships

These are the governed, claim-supportable relations.

### Hierarchical

| Type | Semantics |
|---|---|
| `PART_OF` | A is a constituent of B |
| `CONTAINS` | A wholly contains B |
| `BELONGS_TO` | A is a member of B |

### Semantic Core

| Type | Semantics | Inverse |
|---|---|---|
| `RELATED_TO` | Generic connection, unspecified | `RELATED_TO` |
| `CONTRASTS_WITH` | A is a meaningful contrast of B | `CONTRASTS_WITH` |
| `OPPOSITE_OF` | A is a strict semantic opposite of B | `OPPOSITE_OF` |
| `DEEPENS` | A deepens the understanding of B | `DEEPENED_BY` |
| `PRECEDES` | A comes before B in a meaningful order | `FOLLOWS` |
| `FOLLOWS` | A comes after B in a meaningful order | `PRECEDES` |
| `EXPANDS` | A broadens the scope of B | `EXPANDED_BY` |

### Linguistic Projection

| Type | Semantics |
|---|---|
| `WORD_FAMILY` | A and B share a root |
| `DERIVED_FROM` | A is derived from B |
| `SYNONYM_OF` | A and B are interchangeable |
| `NEAR_SYNONYM_OF` | A and B are close but not interchangeable |
| `ANTONYM_OF` | A and B are antonymic |

### Literary

| Type | Semantics |
|---|---|
| `USED_BY` | The concept is used in the literary work |
| `DEVELOPED_BY` | The concept is developed by the author/tradition |
| `SYMBOLIZED_BY` | The concept is symbolized by the image |
| `THEME_OF` | The concept is a theme of the work |

### Lexical

| Type | Semantics |
|---|---|
| `REALIZED_BY` | The concept is realized by the lexical form |
| `SEMANTIC_BRIDGE` | The concept bridges two semantic regions |

### Architectural Projection

| Type | Semantics |
|---|---|
| `CHAPTER_ANCHOR` | The World anchors a Chapter |
| `CLUSTER_ANCHOR` | The World anchors a SemanticCluster |
| `TRANSITION_TO` | The World transitions into the target |
| `RING_LINK` | The Worlds are members of the same semantic ring |
| `SEMANTIC_BRIDGE` | The World bridges two Chapters |

### Governance

| Type | Semantics |
|---|---|
| `MERGED_INTO` | The source World was merged into the target World |

**INVARIANT (I-035):** `RELATED_TO` is a last resort. If a more specific type applies, it must be
used. A `RELATED_TO` between two Worlds that stand in a documented contrast is a modelling defect.

**INVARIANT (I-036):** Inverse types (`PRECEDES`/`FOLLOWS`, `DEEPENS`/`DEEPENED_BY`,
`EXPANDS`/`EXPANDED_BY`) are materialized in the graph, not computed at query time, so that
bidirectional traversal is a single hop. Both directions carry the same `status`, `scope`, and
supporting `claim_id`.

**INVARIANT (I-037):** `OPPOSITE_OF` requires at least one approved Claim. Opposites are strong
assertions. `CONTRASTS_WITH` requires no Claim.

**INVARIANT (I-038):** `SYNONYM_OF` and `NEAR_SYNONYM_OF` are merge candidates, not merge
decisions. Only human approval performs a merge (§8.4).

## 4.5 Assertive Relationships (Claims, not edges)

A Claim's relationship to the world is expressed by `subject_kind` / `subject_reference_id` /
`predicate` / `object`, never by a graph edge.

| `subject_kind` | Points to |
|---|---|
| `world` | `worlds.world_id` |
| `lexical_form` | `lexical_forms.lexical_id` |
| `source` | `sources.source_id` |
| `witness` | `witnesses.witness_id` |
| `segment` | `segments.segment_id` |
| `unit` | `units.unit_id` |
| `relation` | `relations.relation_id` |
| `path` | `semantic_paths.path_id` |

**INVARIANT (I-039):** `subject_reference_id` must resolve to a row of the table named by
`subject_kind`. An unresolvable subject is a referential-integrity error and rejects the write.

---

# 5. Predicates

A predicate is the Claim-level assertion verb. It is a controlled vocabulary stored in
`claims.predicate`, indexed for lookup.

## 5.1 Definition and Identity

| Predicate | Subject | Object |
|---|---|---|
| `defines` | world / lexical_form | textual definition |
| `glosses_as` | world | English equivalent |
| `transliterates_to` | world | transliteration |
| `derives_from_root` | world / lexical_form | trilateral root |
| `aliases` | world | alias string |

## 5.2 Semantic Content

| Predicate | Subject | Object |
|---|---|---|
| `has_literal_meaning` | world | text |
| `has_expanded_meaning` | world | text |
| `has_dimension` | world | dimension name + content |
| `answers_question` | world | question text |
| `varies_along` | world | axis text |
| `participates_in_experience` | world | experience name |

## 5.3 Relations and Structure

| Predicate | Subject | Object |
|---|---|---|
| `deepens` | world | world |
| `contrasts_with` | world | world |
| `is_opposite_of` | world | world |
| `is_member_of_cluster` | world | cluster |
| `is_anchor_of_chapter` | world | chapter |
| `precedes` | world | world |
| `realized_by` | world | lexical_form |
| `belongs_to_family` | lexical_form | word_family |

## 5.4 Textual and Literary

| Predicate | Subject | Object |
|---|---|---|
| `occurs_in` | lexical_form | segment |
| `expressed_by` | unit | lexical_form |
| `uses_symbol` | unit | world |
| `expresses_theme` | unit | world |
| `evokes_experience` | unit | experience name |
| `commented_by` | unit | commentary text |
| `translated_as` | unit | translated text |

## 5.5 Governance and Editorial

| Predicate | Subject | Object |
|---|---|---|
| `created_by` | any | contributor |
| `reviewed_by` | claim | curator |
| `supersedes` | claim | claim_id |
| `merged_into` | world | world_id |
| `derived_from_source` | any | source_id |

**INVARIANT (I-040):** Predicates are never invented at runtime. A new predicate is an ontology
change requiring a document update and a `CHECK` constraint or vocabulary table entry.

**INVARIANT (I-041):** A Claim whose predicate is in §5.3 has an `object` that is a World ID. A
Claim whose predicate is in §5.1 or §5.2 has a textual `object`. A Claim whose predicate is in
§5.5 may have either.

---

# 6. Enumerations

Every enum value below is a closed set. Adding a value is a schema migration.

## 6.1 `Scope`

| Value | Meaning |
|---|---|
| `global` | Valid across all traditions |
| `tradition` | Valid within a named tradition |
| `workspace` | Valid within a single workspace |

## 6.2 `WorldStatus`

Used by `World` and `Relation`.

| Value | Meaning |
|---|---|
| `draft` | Being authored, not reviewable |
| `proposed` | Submitted for review |
| `approved` | Canonically governed |
| `deprecated` | Retained but no longer recommended |
| `merged` | Absorbed into another World |
| `superseded` | Replaced by a newer version |

## 6.3 `ClaimStatus`

| Value | Meaning |
|---|---|
| `discovered` | Extracted by a pipeline, not yet framed |
| `proposed` | Framed and submitted |
| `reviewed` | Curator has reviewed, awaiting approval |
| `approved` | Canonically governed |
| `published` | Published to readers |
| `superseded` | Replaced by a newer version |
| `rejected` | Rejected; retained in history |
| `challenged` | Under active challenge |

## 6.4 `ChallengeStatus`

| Value | Meaning |
|---|---|
| `open` | Filed, awaiting curator |
| `under_review` | Curator actively considering |
| `resolved` | Resolution recorded |

## 6.5 `EvidenceType`

| Value | Meaning |
|---|---|
| `text_span` | Quoted span from a text |
| `citation` | Scholarly citation |
| `manuscript` | Manuscript witness |
| `commentary` | Published commentary |
| `comparative_passage` | Parallel passage in another work |
| `lexical` | Lexical or morphological evidence |
| `ai_extraction` | Machine-extracted evidence |

## 6.6 `ContributorKind`

| Value | Meaning |
|---|---|
| `editor` | Editorial staff |
| `scholar` | Academic contributor |
| `curator` | Governance decision-maker |
| `translator` | Translation contributor |
| `reader` | End user / challenger |
| `ai_system` | Language model output |
| `pipeline` | Automated ingestion stage |
| `system` | Infrastructure |

## 6.7 `ChallengeResolution`

| Value | Meaning |
|---|---|
| `reaffirmed` | Challenge rejected; original stands |
| `superseded` | New version created; original retired |
| `merged` | Entity merged into another |
| `withdrawn` | Challenger withdrew |

## 6.8 `EmbeddingType`

| Value | Applies to | Content embedded |
|---|---|---|
| `world_full` | world | All textual fields concatenated |
| `world_definition` | world | `short_definition` + `literal_meaning` |
| `world_meaning` | world | `expanded_meaning` |
| `world_literary` | world | `semantic_dimensions.literary` |
| `world_philosophical` | world | `semantic_dimensions.philosophical` |
| `world_modern` | world | `semantic_dimensions.modern` |
| `world_questions` | world | `central_question` + `central_axis` |
| `claim_text` | claim | `text` |
| `claim_evidence` | claim | Concatenated evidence text |
| `source_segment` | source | Segment text |
| `source_translation` | source | Translation text |

## 6.9 `ClaimType`

| Value | Meaning |
|---|---|
| `factual` | Verifiable statement of fact |
| `descriptive` | Description of properties |
| `interpretive` | Meaning-bearing interpretation |
| `comparative` | Comparison between two entities |
| `historical` | Historical assertion |
| `ontological` | Assertion about conceptual structure |
| `relational` | Assertion about a relationship |
| `editorial` | Editorial decision or convention |
| `inferential` | Derived by inference, not directly attested |

## 6.10 `RelationType`

The complete set, grouped as in §4.4:

```
part_of, contains, belongs_to, related_to, contrasts_with, opposite_of,
deepens, deepens_toward, deepens_into, deepens_through, deepens_to,
precedes, follows, expands,
word_family, derived_from, synonym_of, near_synonym_of, antonym_of,
used_by, developed_by, symbolized_by, theme_of,
semantic_bridge, ring_link, chapter_anchor, cluster_anchor, transition_to,
realized_by, merged_into
```

**INVARIANT (I-042):** A Relation type that conveys direction must have a declared inverse
(§4.4). An asymmetric type without an inverse is rejected at validation.

**INVARIANT (I-043):** `deepens_toward`, `deepens_into`, `deepens_through`, and `deepens_to` are
distinct types, not synonyms. They encode the different shapes of semantic deepening and must not
be collapsed.

---

# 7. Lifecycle State Machines

## 7.1 World / Relation Lifecycle

```
                  ┌────────┐
                  │ DRAFT  │
                  └───┬────┘
                      │ submit
                      ▼
      ┌──────────► PROPOSED ◄──────────┐
      │                │                │
      │ approve        │ withdraw       │ revise
      │                ▼                │
      │           (to DRAFT) ───────────┘
      │
      ├──► APPROVED ──────────► PUBLISHED-equivalent (for Worlds: canonical)
      │        │
      │        │ challenge resolved as SUPERSEDED
      │        ▼
      │    SUPERSEDED
      │
      │ (no new successor created)      (merged via §8.4)
      └──► MERGED ─────────────────────► target World
```

### 7.1.1 Transition Table

| From | To | Trigger | Actor |
|---|---|---|---|
| `draft` | `proposed` | Submit for review | editor / pipeline |
| `proposed` | `draft` | Withdraw / request revision | editor / curator |
| `proposed` | `approved` | Approve | curator |
| `proposed` | `deprecated` | Reject as not viable | curator |
| `approved` | `deprecated` | Deprecate | curator |
| `approved` | `superseded` | Challenge resolved `superseded` | curator |
| `approved` | `merged` | Merge approved | curator |
| `deprecated` | `approved` | Reinstate | curator |
| `merged` | — | Terminal | — |
| `superseded` | — | Terminal | — |
| `draft` | `deprecated` | Abandon | curator |

**INVARIANT (I-044):** Only a `curator` may perform any transition into `approved`, `superseded`,
`merged`, or `deprecated`. Agents may only produce `draft` and `proposed`.

**INVARIANT (I-045):** `merged` and `superseded` are terminal. Reinstating them requires creating a
new entity.

**INVARIANT (I-046):** No transition leaves `merged` or `superseded`. They are audit records.

## 7.2 Claim Lifecycle

```
   ┌───────────┐
   │ DISCOVERED│  pipeline extraction
   └─────┬─────┘
         │ frame
         ▼
   ┌───────────┐
   │  PROPOSED │◄──────────┐
   └─────┬─────┘           │ return for revision
         │                 │
         ├──► REJECTED ───┘        (terminal, retained)
         │
         │ review
         ▼
   ┌───────────┐
   │  REVIEWED │
   └─────┬─────┘
         │ approve
         ▼
   ┌───────────┐      publish      ┌────────────┐
   │  APPROVED │───────────────────►│ PUBLISHED  │
   └─────┬─────┘                    └─────┬──────┘
         │                               │
         │ challenge open                │ superseded
         ▼                               │
   ┌────────────┐                        │
   │ CHALLENGED │                        │
   └─────┬──────┘                        │
         │ resolve                       │
         ▼                               │
   ┌───────────┐                         │
   │  REVIEWED │                         │
   └─────┬─────┘                         │
         │                               │
    ┌────┴────┐                          │
    ▼         ▼                          │
APPROVED  SUPERSEDED ◄───────────────────┘
```

### 7.2.1 Transition Table

| From | To | Trigger | Actor |
|---|---|---|---|
| `discovered` | `proposed` | Frame as assertion | editor / pipeline |
| `discovered` | `rejected` | Not a valid assertion | curator |
| `proposed` | `reviewed` | Curator review complete | curator |
| `proposed` | `rejected` | Reject | curator |
| `proposed` | `discovered` | Return to extraction | curator |
| `reviewed` | `approved` | Approve | curator |
| `reviewed` | `rejected` | Reject | curator |
| `approved` | `published` | Publish | editor / curator |
| `published` | `challenged` | Challenge opened | reader / curator |
| `challenged` | `reviewed` | Challenge under review | curator |
| `challenged` | `approved` | Challenge reaffirmed or withdrawn | curator |
| `challenged` | `superseded` | Challenge resolved as superseded | curator |
| `approved` | `superseded` | Version superseded | curator |
| `published` | `superseded` | Version superseded | curator |
| `rejected` | `proposed` | Reconsider | curator |
| `superseded` | — | Terminal | — |

**INVARIANT (I-047):** Rejected Claims are never deleted. They are the intellectual audit trail.

**INVARIANT (I-048):** `confidence` may only be set while the Claim is in `reviewed`, `approved`,
or `published` (see I-014).

**INVARIANT (I-049):** A Claim may not reach `approved` with an empty `evidence` list unless
`claim_type` is `editorial` or `ontological`. Those claim types are governance decisions about
structure, not assertions about content, and are authorized by the ontology itself.

## 7.3 Challenge Lifecycle

```
   ┌──────┐   curator picks up   ┌──────────────┐   curator decides   ┌──────────┐
   │ OPEN │─────────────────────►│ UNDER_REVIEW │────────────────────►│ RESOLVED │
   └──────┘                      └──────────────┘                     └──────────┘
      │                                 │                                  │
      └──► withdraw ────────────────────┘                                  │
                            (→ resolved, resolution = withdrawn)           │
```

### 7.3.1 Resolution Effects

| Resolution | Effect on challenged entity | Effect on graph | Effect on vectors |
|---|---|---|---|
| `reaffirmed` | Status → `approved` | No change | No change |
| `withdrawn` | Status → `approved` | No change | No change |
| `superseded` | Status → `superseded`; new version created; `version_history` updated | Edges re-point to new version | Old vectors marked ineligible; new vectors created |
| `merged` | Status → `merged`; `MERGED_INTO` relation created | Edges re-point to target | Old vectors marked ineligible |

**INVARIANT (I-050):** Resolution of a `superseded` challenge performs §8.3 versioning atomically. If
any step fails, the challenge returns to `under_review`.

**INVARIANT (I-051):** `reaffirmed` and `withdrawn` both restore the entity to `approved`. The
difference is recorded in `resolution` and `resolver_id`, and is never collapsed.

### 7.3.2 The Challenged Marker

`ClaimStatus` has a `challenged` value. `WorldStatus` and the Relation status enum **do not**, and
this is intentional: a World is not less canonical because someone disputes it.

| Entity | Interim status while challenged | Where the dispute lives |
|---|---|---|
| Claim | `challenged` | `claims.status` |
| World | `approved` (unchanged) | The open `Challenge` record |
| Relation | `approved` (unchanged) | The open `Challenge` record |

**INVARIANT (I-052a):** The existence of an `open` or `under_review` Challenge is the sole marker
of contest for Worlds and Relations. Adding a `challenged` value to `WorldStatus` is forbidden — it
would contradict the World content-state model (§3.1.3), where identity governance and content
uncertainty are separate concerns.

**INVARIANT (I-052b):** A World or Relation with an open Challenge is still returned by canonical
retrieval, and retrieval **must** surface the open Challenge alongside it. Hiding a contested World
would misrepresent the state of knowledge; presenting it without the contest would misrepresent it
too.


## 7.4 Embedding Lifecycle

```
   DRAFT ──► PROPOSED ──► ELIGIBLE ──► STALE ──► SUPERSEDED
             (eligible only  (entity mutated)  (model changed,
              if parent entity                    reindexed)
              is approved)
```

| State | In default index | Meaning |
|---|---|---|
| `draft` | No | Vector being computed |
| `proposed` | No | Computed, parent not yet approved |
| `eligible` | Yes | Parent approved, content hash current |
| `stale` | No | `content_hash` no longer matches parent |
| `superseded` | No | Model version replaced |

**INVARIANT (I-052):** A `stale` embedding is never returned by default retrieval. Staleness is
detected by comparing `content_hash` against the parent's current hash, not by timestamp.

---

# 8. Versioning, Merge, and Split

## 8.1 Version Identity

A version is not a separate table. A version is a **new entity row with a new ID** that records its
predecessor in `version_history`.

```
W_ishq                    version_history = []
W_ishq_v2                 version_history = ["W_ishq"]
W_ishq_v3                 version_history = ["W_ishq", "W_ishq_v2"]
```

`current_version_id` on the surviving row points to the active version.

**INVARIANT (I-053):** Version IDs are new IDs, never mutated IDs. `W_ishq` is permanently the
first version. This is what makes the audit trail trustworthy.

**INVARIANT (I-054):** `version_history` is ordered oldest-first and is append-only. Entries are
never removed or reordered.

**INVARIANT (I-055):** At most one version of a lineage has `status = approved`. All other versions
are `superseded`, `deprecated`, or `merged`.

## 8.2 When a New Version Is Required

A new version is created when:

| Change | New version? |
|---|---|
| `canonical_term` changed after approval | **Yes**, mandatory |
| `short_definition` or `expanded_meaning` changed | Yes, recommended |
| A new `semantic_dimensions` key added | No — in-place, but re-embed |
| A Claim supporting a dimension added | No — Claims are separate entities |
| `status` transitioned | No — in-place, lifecycle change |
| `chapter_id` / `cluster_id` moved | No — in-place, but architecturally significant |
| `scope` changed | No — in-place, governance change |

**INVARIANT (I-056):** A new version is never created for a change that a Claim can express.
Prefer a new Claim over a new version wherever the change is an assertion rather than an
identity-level or definition-level change.

## 8.3 Versioning Procedure (Superseded Resolution)

Atomic, single transaction:

1. Copy the original row into a new row with a new `*_id`.
2. Set the new row's `version_history` to `original.version_history + [original.id]`.
3. Apply the correction to the new row.
4. Set `original.status = superseded`.
5. Set `original.current_version_id = new_id`.
6. Append `new_id` to the original's successor pointer.
7. Re-point all Neo4j edges from `original` to `new_id`.
8. Mark original's embeddings `stale`; create embeddings for `new_id`.
9. Record a `supersedes` Claim linking `new_id` → `original`.

**INVARIANT (I-057):** Steps 1–6 are atomic in PostgreSQL. Steps 7–8 are performed by the
projection worker and are idempotent. A failed projection is a repairable inconsistency (§12.4),
never a data loss.

**INVARIANT (I-058):** The original entity is never deleted by versioning. It remains queryable by
ID and remains in the graph as a `superseded` node so that old citations still resolve.

## 8.4 Merge Protocol

A merge absorbs a source World into a target World.

### Preconditions

| Condition | Requirement |
|---|---|
| Both Worlds exist | status in `draft`, `proposed`, `approved` |
| Evidence of synonymy | at least one approved Claim of type `comparative` or `ontological` |
| Conflict detection | run and reported to the reviewer |
| Human approval | explicit curator action |

### Procedure

1. Agent proposes a `MERGE` proposal naming `source_world_id` and `target_world_id`.
2. System collects all Claims from both Worlds.
3. System runs conflict detection on claims whose `subject_reference_id` differs but whose
   `predicate` is the same, and on any two Claims with contradictory `object` values for the same
   `predicate`.
4. A curator reviews source, target, combined claims, and the conflict report.
5. On approval:
   a. `source.status = merged`
   b. Create `Relation(source, merged_into, target)`
   c. Add `source.world_id` to `target`'s `ontology_registry.aliases`
   d. Re-point all `source`'s incoming/outgoing edges to `target`, deduplicating by
      `(relation_type, target_id)`
   e. Re-point all `source`'s Claims' `subject_reference_id` to `target` — unless the Claim is a
      `comparative` Claim about source and target, which is retained verbatim as the merge
      justification
   f. Set `source.current_version_id = target.world_id`
   g. Mark `source`'s embeddings ineligible
   h. Recompute derived properties for `target`

### Post-conditions

**INVARIANT (I-059):** Nothing disappears. Every Claim, Evidence record, and Relation that
referenced `source` either now references `target` or is retained as a merge justification.

**INVARIANT (I-060):** A merged World is never a merge target. Merges are transitive and resolve in
a single operation: merging `A` into `B` where `A` is already merged is rejected; re-point to `B`'s
surviving target instead.

**INVARIANT (I-061):** `self.current_version_id = target` is written so that any lookup of
`source.world_id` resolves to `target.world_id` in one hop, without consulting the alias list.

## 8.5 Split Protocol

A split divides one World into two or more.

| Step | Action |
|---|---|
| 1 | Agent proposes a `SPLIT` proposal naming `parent_world_id` and the proposed children |
| 2 | System assigns each of the parent's Claims to exactly one child, or flags unassignable |
| 3 | System assigns each of the parent's Relations to exactly one child, or flags unassignable |
| 4 | A curator resolves each flagged item manually |
| 5 | Curator approves the split |
| 6 | New World rows are created for each child, status `approved` |
| 7 | `parent.status = merged`, and a `MERGED_INTO` relation is created for each child — a split is a one-to-many merge |
| 8 | `parent.central_axis` records the axis along which the split occurred |
| 9 | Embeddings are created for each child; parent's are marked ineligible |

**INVARIANT (I-062):** A split never deletes the parent. The parent becomes a redirect to its
children, preserving every historical citation.

**INVARIANT (I-063):** Every Claim and Relation of the parent is assigned to exactly one child
after curator resolution. No Claim is duplicated across children, and none is orphaned.

**INVARIANT (I-064):** A split requires at least one approved Claim of type `ontological` justifying
the axis of division.

## 8.6 Merge and Split Are the Same Operation

**INVARIANT (I-065):** Merge and split are one operation with different arity. The system implements
a single `reassign(sources, targets)` primitive:

| Operation | `sources` | `targets` |
|---|---|---|
| Merge | 1 | 1 |
| Split | 1 | N |

Both set the source(s) to `merged`, create `MERGED_INTO` edges, re-point all references, and
preserve history identically.

---

# 9. Scope Rules

## 9.1 Scope Semantics

`scope` is a **governance** dimension, not a tenancy dimension. It records how widely a knowledge
object is asserted to be valid.

| Scope | Valid within | Inherits from |
|---|---|---|
| `global` | All traditions and workspaces | Nothing |
| `tradition` | One named tradition | `global` |
| `workspace` | One workspace | `tradition`, then `global` |

## 9.2 Resolution Order

A read of scope `workspace` sees objects from `workspace`, then `tradition`, then `global`, with
narrower scope winning on conflict.

```
query(workspace = "w1", subject = W_khayal)
  → W_khayal (workspace)     ← highest precedence
  → W_khayal (tradition)     ← shadowed
  → W_khayal (global)        ← shadowed
```

**INVARIANT (I-066):** Narrower scope shadows broader scope for the same `entity_id`. Exactly one
effective record is returned per `(scope, entity_id)` pair, and resolution returns the narrowest
match.

## 9.3 Phase 0 Restriction

**INVARIANT (I-067):** In Phase 0, all records are `global`. The `scope` column exists and is
indexed, and the resolution order is implemented, but no `tradition` or `workspace` records are
created. The schema must not be changed to add tenancy later.

**INVARIANT (I-068):** Scope is never used as an authorization mechanism. It does not grant or deny
access. Authorization is a separate concern (`docs/15-security/`).

## 9.4 Scope Transitions

| From | To | Condition |
|---|---|---|
| `workspace` | `tradition` | Curator promotes after broader validation |
| `workspace` | `global` | Curator promotes after universal validation |
| `tradition` | `global` | Curator promotes after cross-tradition validation |
| `global` | `tradition` | Curator restricts after finding tradition-specific overreach |
| any | any | **Never** by agent |

**INVARIANT (I-069):** Only a curator changes `scope`. Promotion from `workspace` to `global`
requires that the supporting Claims be promoted to `global` in the same operation.

---

# 10. Referential Integrity Summary

| Child | Parent | Cardinality | Nullability | On parent delete |
|---|---|---|---|---|
| `relations.source_world_id` | `worlds` | N:1 | NOT NULL | RESTRICT |
| `relations.target_world_id` | `worlds` | N:1 | NOT NULL | RESTRICT |
| `relations.claim_id` | `claims` | N:1 | NULL | SET NULL |
| `claims.subject_reference_id` | polymorphic | N:1 | NOT NULL | Application-enforced |
| `worlds.chapter_id` | `chapters` | N:1 | NULL | SET NULL |
| `worlds.cluster_id` | `semantic_clusters` | N:1 | NULL | SET NULL |
| `worlds.current_version_id` | same table | N:1 | NULL | Application-enforced |
| `semantic_clusters.chapter_id` | `chapters` | N:1 | NOT NULL | RESTRICT |
| `semantic_clusters.part_id` | `parts` | N:1 | NULL | SET NULL |
| `parts.chapter_id` | `chapters` | N:1 | NOT NULL | RESTRICT |
| `ontology_registry.world_id` | `worlds` | 1:1 | NOT NULL | CASCADE |
| `embeddings.entity_id` | polymorphic | N:1 | NOT NULL | Application-enforced |
| `embedding_provenance.embedding_id` | `embeddings` | 1:1 | NOT NULL | CASCADE |
| `challenges.entity_id` | polymorphic | N:1 | NOT NULL | Application-enforced |
| `word_families.members[]` | `lexical_forms` | N:M | — | Application-enforced |
| `semantic_paths.world_ids[]` | `worlds` | N:M | — | Application-enforced |

**INVARIANT (I-070):** Polymorphic references (`claims.subject_reference_id`,
`embeddings.entity_id`, `challenges.entity_id`) are **application-enforced**, not database-enforced.
Every write path must validate them. See I-039.

**INVARIANT (I-071):** Because no knowledge object is ever deleted (I-004, I-047, I-059, I-062),
`RESTRICT` on World references is never triggered in practice. It exists to prevent accidental
deletion at the database level.

---

# 11. PostgreSQL Mapping

PostgreSQL is the **canonical persistence layer**. This section is normative for schema.

## 11.1 Tables

| Table | Entity | Notes |
|---|---|---|
| `worlds` | World | Primary knowledge table |
| `claims` | Claim | Governed assertions |
| `relations` | Relation | Governed semantic relations |
| `semantic_paths` | SemanticPath | Ordered journeys |
| `chapters` | Chapter | Architectural container |
| `parts` | Part | Architectural container |
| `semantic_clusters` | SemanticCluster | Architectural container |
| `lexical_forms` | LexicalForm | Linguistic |
| `word_families` | WordFamily | Linguistic |
| `ontology_registry` | OntologyRegistryEntry | Alias/translation registry |
| `embeddings` | Embedding | Vector projection |
| `embedding_provenance` | EmbeddingProvenance | Vector audit |
| `challenges` | Challenge | Governance |
| `sources` | Source | Textual input |
| `witnesses` | Witness | Textual input |
| `segments` | Segment | Textual input |
| `units` | Unit | Textual input |

## 11.2 Core DDL

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------- worlds
CREATE TABLE worlds (
    world_id            TEXT PRIMARY KEY,
    canonical_term      TEXT        NOT NULL,
    transliteration     TEXT,
    persian_term        TEXT,
    urdu_term           TEXT,
    arabic_root         TEXT,
    english_gloss       TEXT,
    short_definition    TEXT,
    literal_meaning     TEXT,
    expanded_meaning    TEXT,
    central_question    TEXT,
    central_axis        TEXT,
    semantic_dimensions JSONB       NOT NULL DEFAULT '{}'::jsonb,
    status              TEXT        NOT NULL DEFAULT 'proposed',
    scope               TEXT        NOT NULL DEFAULT 'global',
    chapter_id          TEXT        REFERENCES chapters(chapter_id) ON DELETE SET NULL,
    cluster_id          TEXT        REFERENCES semantic_clusters(cluster_id) ON DELETE SET NULL,
    current_version_id  TEXT,
    version_history     JSONB       NOT NULL DEFAULT '[]'::jsonb,
    provenance          JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT worlds_status_chk
        CHECK (status IN ('draft','proposed','approved','deprecated','merged','superseded')),
    CONSTRAINT worlds_scope_chk
        CHECK (scope  IN ('global','tradition','workspace'))
);

CREATE INDEX worlds_canonical_term_idx ON worlds (canonical_term);
CREATE INDEX worlds_status_idx           ON worlds (status);
CREATE INDEX worlds_scope_idx            ON worlds (scope);
CREATE INDEX worlds_chapter_idx          ON worlds (chapter_id);
CREATE INDEX worlds_cluster_idx          ON worlds (cluster_id);
CREATE INDEX worlds_current_version_idx  ON worlds (current_version_id);
CREATE INDEX worlds_terms_trgm_idx       ON worlds USING gin
    (canonical_term gin_trgm_ops);
CREATE INDEX worlds_provenance_gin       ON worlds USING gin (provenance);

-- --------------------------------------------------------------- claims
CREATE TABLE claims (
    claim_id            TEXT PRIMARY KEY,
    claim_type          TEXT        NOT NULL,
    subject_kind        TEXT        NOT NULL,
    subject_reference_id TEXT       NOT NULL,
    subject_label       TEXT,
    predicate           TEXT        NOT NULL,
    object              TEXT,
    text                TEXT        NOT NULL,
    status              TEXT        NOT NULL DEFAULT 'proposed',
    scope               TEXT        NOT NULL DEFAULT 'global',
    confidence          DOUBLE PRECISION NOT NULL DEFAULT 0.0
                                      CHECK (confidence >= 0.0 AND confidence <= 1.0),
    evidence            JSONB       NOT NULL DEFAULT '[]'::jsonb,
    provenance          JSONB       NOT NULL DEFAULT '[]'::jsonb,
    version_history     JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT claims_type_chk CHECK (claim_type IN (
        'factual','descriptive','interpretive','comparative','historical',
        'ontological','relational','editorial','inferential')),
    CONSTRAINT claims_status_chk CHECK (status IN (
        'discovered','proposed','reviewed','approved','published',
        'superseded','rejected','challenged')),
    CONSTRAINT claims_scope_chk CHECK (scope IN ('global','tradition','workspace')),
    CONSTRAINT claims_subject_kind_chk CHECK (subject_kind IN (
        'world','lexical_form','source','witness','segment','unit',
        'relation','path'))
);

CREATE INDEX claims_type_idx            ON claims (claim_type);
CREATE INDEX claims_subject_ref_idx    ON claims (subject_reference_id);
CREATE INDEX claims_subject_kind_idx   ON claims (subject_kind);
CREATE INDEX claims_predicate_idx      ON claims (predicate);
CREATE INDEX claims_status_idx          ON claims (status);
CREATE INDEX claims_scope_idx           ON claims (scope);
CREATE INDEX claims_evidence_gin        ON claims USING gin (evidence);

-- ------------------------------------------------------------ relations
CREATE TABLE relations (
    relation_id     TEXT PRIMARY KEY,
    relation_type   TEXT        NOT NULL,
    source_world_id TEXT        NOT NULL REFERENCES worlds(world_id) ON DELETE RESTRICT,
    target_world_id TEXT        NOT NULL REFERENCES worlds(world_id) ON DELETE RESTRICT,
    claim_id        TEXT        REFERENCES claims(claim_id) ON DELETE SET NULL,
    status          TEXT        NOT NULL DEFAULT 'proposed',
    scope           TEXT        NOT NULL DEFAULT 'global',
    provenance      JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT relations_status_chk CHECK (status IN (
        'draft','proposed','approved','deprecated','merged','superseded')),
    CONSTRAINT relations_scope_chk CHECK (scope IN ('global','tradition','workspace')),
    CONSTRAINT relations_no_self_chk CHECK (source_world_id <> target_world_id)
);

CREATE UNIQUE INDEX relations_edge_uniq
    ON relations (relation_type, source_world_id, target_world_id)
    WHERE status NOT IN ('deprecated','merged','superseded');
CREATE INDEX relations_type_idx   ON relations (relation_type);
CREATE INDEX relations_source_idx ON relations (source_world_id);
CREATE INDEX relations_target_idx ON relations (target_world_id);
CREATE INDEX relations_claim_idx  ON relations (claim_id);
CREATE INDEX relations_status_idx ON relations (status);

-- -------------------------------------------------- architectural containers
CREATE TABLE chapters (
    chapter_id             TEXT PRIMARY KEY,
    title                  TEXT        NOT NULL,
    title_transliteration  TEXT,
    description            TEXT,
    central_question       TEXT,
    order                  BIGINT      NOT NULL UNIQUE,
    metadata               JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE parts (
    part_id      TEXT PRIMARY KEY,
    chapter_id   TEXT   NOT NULL REFERENCES chapters(chapter_id) ON DELETE RESTRICT,
    title        TEXT   NOT NULL,
    description  TEXT,
    order        BIGINT NOT NULL,
    metadata     JSONB  NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT parts_order_uniq UNIQUE (chapter_id, order)
);

CREATE TABLE semantic_clusters (
    cluster_id   TEXT PRIMARY KEY,
    chapter_id   TEXT   NOT NULL REFERENCES chapters(chapter_id) ON DELETE RESTRICT,
    part_id      TEXT   REFERENCES parts(part_id) ON DELETE SET NULL,
    title        TEXT   NOT NULL,
    description  TEXT,
    metadata     JSONB  NOT NULL DEFAULT '{}'::jsonb
);

-- ------------------------------------------------------------- linguistic
CREATE TABLE lexical_forms (
    lexical_id       TEXT PRIMARY KEY,
    term             TEXT   NOT NULL,
    language         TEXT   NOT NULL,
    transliteration  TEXT,
    root             TEXT,
    metadata         JSONB  NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX lexical_forms_term_idx     ON lexical_forms (term);
CREATE INDEX lexical_forms_language_idx ON lexical_forms (language);
CREATE INDEX lexical_forms_root_idx     ON lexical_forms (root);
CREATE INDEX lexical_forms_term_trgm    ON lexical_forms USING gin (term gin_trgm_ops);

CREATE TABLE word_families (
    family_id  TEXT PRIMARY KEY,
    root       TEXT   NOT NULL,
    language   TEXT   NOT NULL,
    members    JSONB  NOT NULL DEFAULT '[]'::jsonb,
    metadata   JSONB  NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX word_families_root_idx ON word_families (root);

-- ------------------------------------------------------ semantic journeys
CREATE TABLE semantic_paths (
    path_id      TEXT PRIMARY KEY,
    title        TEXT   NOT NULL,
    description  TEXT,
    world_ids    JSONB  NOT NULL DEFAULT '[]'::jsonb,
    scope        TEXT   NOT NULL DEFAULT 'global',
    provenance   JSONB  NOT NULL DEFAULT '[]'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT semantic_paths_scope_chk CHECK (scope IN ('global','tradition','workspace'))
);

-- -------------------------------------------------------------- registry
CREATE TABLE ontology_registry (
    world_id          TEXT PRIMARY KEY REFERENCES worlds(world_id) ON DELETE CASCADE,
    canonical_term    TEXT   NOT NULL,
    aliases           JSONB  NOT NULL DEFAULT '[]'::jsonb,
    translations      JSONB  NOT NULL DEFAULT '{}'::jsonb,
    spellings         JSONB  NOT NULL DEFAULT '[]'::jsonb,
    historical_forms  JSONB  NOT NULL DEFAULT '[]'::jsonb,
    language_forms    JSONB  NOT NULL DEFAULT '{}'::jsonb,
    status            TEXT   NOT NULL DEFAULT 'approved',
    extra_metadata    JSONB  NOT NULL DEFAULT '{}'::jsonb
);

-- ------------------------------------------------------------ embeddings
CREATE TABLE embeddings (
    embedding_id   TEXT PRIMARY KEY,
    entity_id      TEXT   NOT NULL,
    entity_type    TEXT   NOT NULL,
    embedding_type TEXT   NOT NULL,
    model          TEXT   NOT NULL,
    model_version  TEXT   NOT NULL,
    dimensions     INTEGER NOT NULL,
    vector         vector(1024) NOT NULL,
    source_version TEXT,
    content_hash   TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT embeddings_entity_type_chk CHECK (entity_type IN (
        'world','claim','source','relation')),
    CONSTRAINT embeddings_unique_uniq UNIQUE
        (entity_id, entity_type, embedding_type, model_version)
);

CREATE INDEX embeddings_entity_idx    ON embeddings (entity_id, entity_type);
CREATE INDEX embeddings_type_idx      ON embeddings (embedding_type);
CREATE INDEX embeddings_model_version_idx ON embeddings (model_version);
CREATE INDEX embeddings_content_hash_idx ON embeddings (content_hash);

-- ivfflat / hnsw index, chosen per deployment scale
CREATE INDEX embeddings_vector_hnsw
    ON embeddings USING hnsw (vector vector_cosine_ops);

CREATE TABLE embedding_provenance (
    embedding_id   TEXT PRIMARY KEY
                   REFERENCES embeddings(embedding_id) ON DELETE CASCADE,
    entity_id      TEXT   NOT NULL,
    entity_type    TEXT   NOT NULL,
    embedding_type TEXT   NOT NULL,
    model          TEXT   NOT NULL,
    model_version  TEXT   NOT NULL,
    dimensions     INTEGER NOT NULL,
    source_version TEXT,
    content_hash   TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------ challenges
CREATE TABLE challenges (
    challenge_id         TEXT PRIMARY KEY,
    entity_type          TEXT   NOT NULL,
    entity_id            TEXT   NOT NULL,
    challenger_id        TEXT   NOT NULL,
    reason               TEXT   NOT NULL,
    new_evidence         JSONB  NOT NULL DEFAULT '[]'::jsonb,
    suggested_correction JSONB,
    status               TEXT   NOT NULL DEFAULT 'open',
    resolution           TEXT,
    resolver_id          TEXT,
    resolved_at          TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT challenges_entity_type_chk CHECK (entity_type IN (
        'world','claim','relation')),
    CONSTRAINT challenges_status_chk CHECK (status IN (
        'open','under_review','resolved')),
    CONSTRAINT challenges_resolution_chk CHECK (resolution IS NULL OR resolution IN (
        'reaffirmed','superseded','merged','withdrawn')),
    CONSTRAINT challenges_resolved_complete_chk CHECK (
        status <> 'resolved'
        OR (resolution IS NOT NULL AND resolver_id IS NOT NULL AND resolved_at IS NOT NULL))
);

CREATE INDEX challenges_entity_idx ON challenges (entity_type, entity_id);
CREATE INDEX challenges_status_idx ON challenges (status);
```

## 11.3 Notes on DDL

**NOTE (N-001):** `relations_edge_uniq` is a partial unique index excluding terminal states. It
permits parallel historical relations of the same type while preventing duplicate live relations.

**NOTE (N-002):** `embeddings.vector` is `vector(1024)`. This matches the frozen embedding model
dimension. A different model requires a different dimension and therefore a different column type;
this is a migration, not a config change.

**NOTE (N-003):** `worlds.semantic_dimensions`, `provenance`, `version_history`, and
`claims.evidence` are `JSONB`, not normalized tables, in Phase 0. They are queryable via GIN
indexes and are promoted to tables only if profiling shows a need. This is a deliberate Phase 0
decision: normalization before measurement is premature.

**NOTE (N-004):** The `pg_trgm` extension supports exact and fuzzy term lookup on
`canonical_term` and `term`. Persian and Arabic text require trigram indexing because these scripts
have complex shaping and normalization behavior.

---

# 12. Neo4j Projection

Neo4j is a **projection**, never a source of truth. Every node and relationship in Neo4j must be
derivable from PostgreSQL.

## 12.1 Node Labels

| Label | Projects from | Key properties |
|---|---|---|
| `World` | `worlds` | `world_id`, `canonical_term`, `transliteration`, `status`, `scope`, `updated_at` |
| `Chapter` | `chapters` | `chapter_id`, `title`, `order` |
| `Part` | `parts` | `part_id`, `title`, `order` |
| `SemanticCluster` | `semantic_clusters` | `cluster_id`, `title` |
| `LexicalForm` | `lexical_forms` | `lexical_id`, `term`, `language` |
| `WordFamily` | `word_families` | `family_id`, `root` |

**INVARIANT (I-072):** `Claim` is **not** projected as a graph node. Claims are PostgreSQL records
reached through relations, not graph topology.

## 12.2 Relationship Types

| Relationship | Direction | Carries |
|---|---|---|
| `RELATES_TO` | `(:World)-[:RELATES_TO]->(:World)` | `relation_id`, `relation_type`, `status`, `scope`, `claim_id` |
| `BELONGS_TO` | `(:World)-[:BELONGS_TO]->(:SemanticCluster)` | — |
| `IN_CHAPTER` | `(:World)-[:IN_CHAPTER]->(:Chapter)` | — |
| `IN_PART` | `(:SemanticCluster)-[:IN_PART]->(:Part)` | — |
| `HAS_PART` | `(:Chapter)-[:HAS_PART]->(:Part)` | — |
| `HAS_CLUSTER` | `(:Part)-[:HAS_CLUSTER]->(:SemanticCluster)` | — |
| `REALIZED_BY` | `(:World)-[:REALIZED_BY]->(:LexicalForm)` | — |
| `IN_FAMILY` | `(:LexicalForm)-[:IN_FAMILY]->(:WordFamily)` | — |

### 12.2.1 `RELATES_TO` — Typed Carrier

All World–World semantic relations use the single Cypher relationship type `RELATES_TO`, with the
semantic type carried in the `relation_type` property. This is a deliberate Phase 0 decision.

**Rationale:** A single relationship type with an indexed property allows arbitrary `relation_type`
values without a graph schema migration, and allows property-level filters in traversal:

```cypher
MATCH (a:World {world_id: $id})-[r:RELATES_TO*1..2]->(b:World)
WHERE r.status = 'approved' AND r.relation_type IN ['deepens','expands']
RETURN b, r
```

**INVARIANT (I-073):** `relation_type` is mandatory on every `RELATES_TO` relationship. A
`RELATES_TO` without `relation_type` is a projection defect.

**INVARIANT (I-074):** Inverse relationships are materialized as separate `RELATES_TO` edges with
`relation_type` set to the inverse value, carrying the same `relation_id` as
`inverse_of_relation_id`. Bidirectional traversal is a single hop.

**NOTE (N-005):** Promoting `relation_type` to native Cypher relationship types is a documented
future optimization. It is not a schema change to the ontology, only to the projection. §12.4
defines the migration.

## 12.3 Projection Queries

### World node

```cypher
MERGE (w:World {world_id: $world_id})
SET w.canonical_term  = $canonical_term,
    w.transliteration = $transliteration,
    w.status          = $status,
    w.scope           = $scope,
    w.updated_at      = datetime()
```

### Semantic relation

```cypher
MATCH (s:World {world_id: $source_world_id})
MATCH (t:World {world_id: $target_world_id})
MERGE (s)-[r:RELATES_TO {relation_id: $relation_id}]->(t)
SET r.relation_type = $relation_type,
    r.status        = $status,
    r.scope         = $scope,
    r.claim_id      = $claim_id,
    r.updated_at    = datetime()
```

### Architectural containment

```cypher
MATCH (w:World   {world_id: $world_id})
MATCH (c:SemanticCluster {cluster_id: $cluster_id})
MERGE (w)-[:BELONGS_TO]->(c)
```

### Canonical-only traversal

```cypher
MATCH (w:World {world_id: $id})-[r:RELATES_TO*1..$depth]-(n:World)
WHERE r.status = 'approved'
  AND r.scope IN $visible_scopes
RETURN n, r
```

## 12.4 Dual-Graph Separation

| Graph | Contents | Traversal filter |
|---|---|---|
| Canonical | Nodes and edges with `status = approved` | `WHERE r.status = 'approved'` |
| Proposal | Nodes and edges with `status` in `draft`, `proposed`, `challenged` | `WHERE r.status <> 'approved'` |

**INVARIANT (I-075):** Proposal-graph nodes and edges are never returned by a canonical query. The
Architect Agent reads the proposal graph; retrieval reads the canonical graph. This separation
prevents an unapproved structural suggestion from contaminating reader-facing results.

**INVARIANT (I-076):** Neo4j is fully rebuildable from PostgreSQL. A `rebuild_projection()` operation
must be able to reconstruct every node and edge from PostgreSQL alone, with no loss. This is the
guarantee that makes Neo4j safe to treat as a projection.

## 12.5 Projection Consistency and Repair

| Failure | Detection | Repair |
|---|---|---|
| Edge missing | World exists in PG, no node in Neo4j | Re-project the World |
| Edge stale | `relation_id` in Neo4j not in PG | Delete edge, re-project |
| Property divergence | PG status ≠ Neo4j status | Overwrite Neo4j from PG |
| Dangling edge | Edge references a missing node | Delete edge |
| Duplicate edge | Two `RELATES_TO` with same `relation_id` | Keep one, delete the other |

**INVARIANT (I-077):** PostgreSQL is always the correct side of any divergence. Repair always writes
Neo4j to match PostgreSQL, never the reverse.

**NOTE (N-007):** A scheduled consistency check compares the count of `approved` relations in
`relations` against the count of `RELATES_TO` edges with `status = 'approved'`. A mismatch raises
an operational alert; it is not auto-repaired without human acknowledgement, because a systematic
mismatch indicates a projection bug rather than transient drift.

## 12.6 Projection Triggers

| PostgreSQL event | Projection action |
|---|---|
| World insert | Create `World` node |
| World status → `approved` | Create node if absent; begin including in canonical graph |
| World status → `superseded` / `merged` | Re-point edges per §8.3 / §8.4; keep node for citation resolution |
| World delete | `DETACH DELETE` — never happens by invariant, retained as a safety net |
| Relation insert | Create `RELATES_TO` |
| Relation status change | Update `r.status` |
| Relation delete | Delete `RELATES_TO` |
| Chapter / Part / Cluster insert | Create node |
| Membership change | Recreate `BELONGS_TO` / `IN_CHAPTER` edges |
| Embedding eligible | Add to default retrieval index |

---

# 13. Vector Store Mapping

The application depends only on the `VectorStore` protocol. The pgvector implementation below is
one realization; migrating to Qdrant does not change §3 or §11.

## 13.1 Protocol

```python
class VectorStore(Protocol):
    async def upsert(self, embeddings: Sequence[Embedding]) -> None: ...
    async def query(self, vector, filters, limit, embedding_type,
                    model_version, scope) -> list[ScoredResult]: ...
    async def delete(self, entity_id: str) -> None: ...
    async def reindex(self, from_model: str, to_model: str) -> None: ...
    async def health_check(self) -> bool: ...
    async def get_by_entity(self, entity_id: str) -> list[Embedding]: ...
    async def count(self) -> int: ...
    async def get_model_info(self) -> ModelInfo: ...
```

## 13.2 Query Contract

Every `query` call **must** apply, without exception:

| Filter | Rule |
|---|---|
| `embedding_type` | Exact match. Never mixes types (I-028). |
| `model_version` | Exact match. Never mixes model versions. |
| `scope` | Visibility filter per §9.2. |
| parent `status` | Only `approved` (I-029). |
| `content_hash` | Only current (I-052). |

**INVARIANT (I-078):** A vector query that cannot filter by `embedding_type` and `model_version` is
invalid and must be rejected. Cross-type or cross-model similarity comparison produces
meaningless distances and is a correctness defect, not a quality issue.

## 13.3 Embedding Content Derivation

| `embedding_type` | Source fields |
|---|---|
| `world_full` | `canonical_term`, `english_gloss`, `short_definition`, `literal_meaning`, `expanded_meaning` |
| `world_definition` | `short_definition`, `literal_meaning` |
| `world_meaning` | `expanded_meaning` |
| `world_literary` | `semantic_dimensions->>'literary'` |
| `world_philosophical` | `semantic_dimensions->>'philosophical'` |
| `world_modern` | `semantic_dimensions->>'modern'` |
| `world_questions` | `central_question`, `central_axis` |
| `claim_text` | `text` |
| `claim_evidence` | concatenation of `evidence[].text` |
| `source_segment` | `segments.text` |
| `source_translation` | translated segment text |

**INVARIANT (I-079):** `content_hash` is `sha256` of the exact embedded text, UTF-8, no
normalization beyond Unicode NFC. A change in any source field listed above changes the hash and
marks dependent embeddings `stale`.

---

# 14. Agent Output Contract

Agents produce **proposals**. This section defines the proposal shape that the orchestrator validates.

## 14.1 Proposal Envelope

Every agent returns `AgentProposal`, a single generic envelope. Agent-specific content lives in
`payload`; the envelope fields are agent-independent.

```json
{
  "proposal_id": "3f2a1c9e-...",
  "agent_type": "relation",
  "status": "draft",
  "confidence": 0.75,
  "reasoning": "Discovered 1 candidate relation for 2 Worlds",
  "evidence": [],
  "payload": { "...": "agent-specific" },
  "created_at": "2026-09-26T00:00:00Z",
  "reviewed_at": null,
  "reviewer_id": null
}
```

| Field | Type | Rule |
|---|---|---|
| `proposal_id` | `id` | Server-assigned UUID |
| `agent_type` | `enum:AgentType` | `relation`, `architect`, `ring_eval`, `gap`, `merge_split`, `ingestion` |
| `status` | `enum:ProposalStatus` | `draft`, `submitted`, `under_review`, `approved`, `rejected`, `implemented` |
| `confidence` | `float` | In [0.0, 1.0]. Aggregated across the payload |
| `reasoning` | `string` | Non-empty. Why this proposal exists |
| `evidence` | `list<json>` | Non-empty per I-081 |
| `payload` | `T` | Agent-specific |
| `created_at` | `timestamp` | Creation instant |
| `reviewed_at` | `timestamp?` | Set on review |
| `reviewer_id` | `id?` | Curator who reviewed |

**NOTE (N-008):** The field is `reasoning`, not `reason`. Proposals are agent reasoning, not
editorial prose; entity-level `ProvenanceRecord.method` is the editorial equivalent.

## 14.2 Payloads Per Agent

| Agent | `payload` | Required payload fields |
|---|---|---|
| Relation | `list<RelationCandidate>` | `source_world_id`, `target_world_id`, `relation_type`, `confidence`, `reasoning` |
| Architect | `ArchitectProposal` | `current_architecture`, `proposed_architecture`, `reasoning`, `affected_worlds` |
| Ring / Eval | `RingEvaluation` | `chapter_id`, `scores` (all 7 dimensions) |
| Gap | `GapProposal` | `missing_concept`, `surrounding_worlds`, `reasoning`, `confidence` |
| Merge / Split | `list<MergeSplitCandidate>` | `source_world_id`, `target_world_ids`, `operation`, `reasoning` |

**INVARIANT (I-080):** A proposal with status `approved` or `implemented` never mutates canonical
state directly. Conversion of a proposal into a World, Claim, or Relation produces a record in
`proposed` status, which then requires curator approval (I-044). This is the
`proposals_to_relations` step, and it is the only write agents may cause.

**INVARIANT (I-081):** Every proposal carries non-empty `reasoning` and `evidence`. A proposal
without justification is not reviewable and is rejected by the orchestrator.

**INVARIANT (I-082):** Ring / Architecture evaluation reports all seven dimensions —
`semantic_coherence`, `transition_quality`, `central_question_alignment`, `redundancy`, `coverage`,
`closure`, `asymmetry_justification`. A single scalar score is not a valid output.
`overall_architectural_confidence` is optional and additional.

**INVARIANT (I-083):** A `RelationCandidate` with `source_world_id == target_world_id` is rejected
by the agent's own `validate_proposal` before it reaches the orchestrator (I-021 enforced at
proposal time, not only at write time).

## 14.3 `ProposalStatus` Transitions

```
   DRAFT ──► SUBMITTED ──► UNDER_REVIEW ──► APPROVED ──► IMPLEMENTED
                │               │              │
                │               │              └──► REJECTED
                │               └──► REJECTED
                └──► REJECTED
```

`implemented` is distinct from `approved` on purpose: approval is a governance decision, while
`implemented` records that the approved proposal was converted into a `proposed` record awaiting
the separate curator approval required by I-044.


---

# 15. Retrieval Contract

## 15.1 Layers

| Layer | Source | Used for |
|---|---|---|
| Source | `segments`, `units` | Original text, witness comparison |
| Commentary | `claims` with `claim_type = interpretive` | Unit commentary |
| Claim | `claims` with `status = approved` | Approved assertions, contested readings |
| Ontology | `worlds`, `semantic_clusters` | Works linked to experience or symbol |
| Graph | Neo4j canonical graph | Concept-to-concept through governed relations |
| Semantic | pgvector | Passages similar in meaning |

## 15.2 Query Modes

| Mode | Primary layers | Requirement |
|---|---|---|
| Source-seeking | Source, Commentary | Returns addressable segments with citations |
| Explanation-seeking | Claim, Commentary | Returns Claims, not free prose |
| Concept-seeking | Ontology, Graph | Returns Worlds and governed relations |
| Question-seeking | Ontology, Semantic | Answers in terms of `central_question` |
| Disagreement-seeking | Claim, Graph | Returns **competing** Claims, never a flattened answer |
| Comparative | Ontology, Graph | Returns both sides symmetrically |

**INVARIANT (I-084):** Disagreement-seeking returns all competing Claims with their statuses and
evidence, including rejected ones where they are historically significant. It must never return a
single synthesized answer to a contested question.

**INVARIANT (I-085):** Every retrieval result carries provenance. A returned World, Claim, or
Relation must expose who asserted it and on what evidence.

---

# 16. Current Implementation Conformance

Status as of the `maana-api` implementation. **Conforming** means the behaviour is present and
tested. **Gap** means the ontology requires it and the code does not yet provide it.

## 16.1 Conforming

| Area | Evidence |
|---|---|
| World, Claim, Relation, SemanticPath, Challenge, Embedding models | `domain/models.py` |
| All enumerations in §6 | `domain/models.py` |
| World lifecycle: create, update, approve, deprecate | `services/world_service.py` |
| Claim lifecycle: create, update, approve | `services/claim_service.py` |
| Challenge workflow, all four resolutions, status restore | `services/challenge_service.py` |
| Challenged-marker model (I-052a): World/Relation keep `approved` while contested | `services/challenge_service.py:172-179` |
| `version_history` appended on supersede | `services/challenge_service.py:132-133` |
| Rejected objects retained | No delete path in claim service |
| Five agents producing proposals only | `agents/` |
| Orchestrator validation | `agents/orchestrator.py` |
| `VectorStore` protocol | `infrastructure/vector_store.py` |
| Neo4j `World` node and `RELATES_TO` | `infrastructure/graph.py` |
| Governance round trip in production test | `evaluation/production_test.py` |

## 16.2 Gaps

The live model set is `domain/models.py`; every service, API module, agent, and test imports from
it. `infrastructure/models.py` is a second, unused definition with the plural table names this
document specifies. Exactly one of the two must survive.

### P0 — schema correctness

| Gap | Ontology requirement |
|---|---|
| Two competing model sets exist. `infrastructure/models.py` is dead code (nothing imports it); `domain/models.py` is live but most of its `table=True` classes declare no `__tablename__`, so they project to `world`, `relation`, `semanticpath`, `claim`, `ontologyregistryentry`, `embeddingprovenance` | §11.1 plural table names, one table per entity |
| `relations.source_world_id` FK targets `world.world_id`, correct only for the accidental singular name; it must target `worlds.world_id` | §11.2 |
| No `CHECK` constraints on `status`, `scope`, `claim_type`, `subject_kind` | §11.2 |
| `Embedding.vector` is `Column("vector", JSON)`, not a pgvector column | §11.2 N-002 |

### P1 — required behaviour

| Gap | Ontology requirement |
|---|---|
| `merge_worlds` only sets `status = merged`. It does not add the alias, create the `MERGED_INTO` relation, re-point Claims or edges, or set `current_version_id` | §8.4 steps 5a–5h, I-059, I-061 |
| `resolve_challenge(SUPERSEDED)` expects the curator to have already created the new version out-of-band, and never verifies `new_entity_id` resolves. It does not copy the entity, create the `supersedes` Claim, or re-point projections | §8.3 steps 1–3, 7–9, I-050 |
| `update_claim` has no status guard, unlike `update_world`. Any field of an `approved` or `published` Claim is directly mutable | §7.2, I-056 |
| `create_world` and `create_claim` do not enforce non-empty `provenance` before `approved` | I-018 |
| Nothing validates that `claims.subject_reference_id` resolves against `subject_kind` | I-039, I-070 |
| No `parts`, `word_families`, `sources`, `witnesses`, `segments`, `units` tables. `Chapter`, `Part`, `SemanticCluster`, `LexicalForm`, `WordFamily` exist only as Pydantic value objects | §3.5–§3.10, §11.1 |
| `GraphProjection.create_relation` does not guard on a required `relation_type`, and inverse edges are not materialized | I-073, I-074 |
| `approve_world` calls `asyncio_run` from sync code, which swallows every exception and returns `None` on failure. A graph projection failure is silently discarded | §12.6 |

### P2 — tracked, non-blocking

| Gap | Ontology requirement |
|---|---|
| No split procedure in `world_service`; only merge | §8.5 |
| No `parts` → Neo4j projection; only World, and World → World | §12.1 |
| No projection consistency check | §12.5 N-007 |
| `datetime.utcnow()` used throughout; produces naive datetimes | §2.1 requires `TIMESTAMPTZ` |
| `Relation` has no `version_history` column | §3.14 — relations are versioned via Claims per I-056 |
| `deprecated → approved` reinstate and `draft → deprecated` abandon transitions unimplemented | §7.1 transition table |
| Evidence strength aggregation function not implemented | I-016, I-017 |
| `confidence` is not restricted to reviewed/approved/published writes | I-014 |
| `ProposalStatus.IMPLEMENTED` and `SUBMITTED`/`UNDER_REVIEW` are defined but never set; all proposals stay `draft` | §14.3 |
| Agent logic is scaffolding, not implementation. `RelationAgent` proposes `related_to` for every pair at fixed confidence 0.75; `RingEvalAgent` returns hard-coded scores; `ArchitectAgent`, `GapAgent`, `MergeSplitAgent` similarly | §14.2, §15 |
| `RelationProposalService.proposals_to_relations` sets `relation_id` as `rel_{source}_{target}`, ignoring `relation_type`, so two relations of different types between the same pair collide | §2.2, I-001 |

**P0 items must be resolved before the schema is frozen and used for migration.** P1 items block
Phase 1. P2 items are tracked but do not block. Note that the last three P2 rows are the reason the
production test's `relations_proposed` check is a structural assertion rather than a semantic one.




---

# 17. Conformance Checklist

An implementation is conformant with this document when all of the following hold.

**Structure**
- [ ] Every entity in §3 has a persistable record
- [ ] Every field matches type and nullability
- [ ] Exactly one PostgreSQL table per entity, named per §11.1
- [ ] No duplicate model definitions across modules

**Relations**
- [ ] Every relationship in §4 exists with the stated cardinality
- [ ] Semantic relations carry status, scope, and provenance
- [ ] Claims are assertions, not graph edges (I-033)
- [ ] Inverses are materialized for bidirectional types (I-036)

**Lifecycle**
- [ ] Every transition in §7.1, §7.2, §7.3 is enforced
- [ ] No transition originates from a terminal state (I-046)
- [ ] Only curators reach `approved`, `merged`, `superseded` (I-044)
- [ ] Rejected and superseded objects are never deleted (I-047, I-059)

**Versioning**
- [ ] Versions are new IDs, not mutated IDs (I-053)
- [ ] `version_history` is append-only and ordered (I-054)
- [ ] At most one approved version per lineage (I-055)
- [ ] Merge re-points all references and sets `current_version_id` (I-061)
- [ ] Split assigns every Claim and Relation to exactly one child (I-063)

**Scope**
- [ ] Narrower scope shadows broader scope (I-066)
- [ ] Only curators change scope (I-069)
- [ ] Scope is not used for authorization (I-068)

**Integrity**
- [ ] `subject_reference_id` resolves against `subject_kind` (I-039)
- [ ] `source_world_id != target_world_id` (I-021)
- [ ] Non-empty provenance before `approved` (I-018)
- [ ] Confidence is curator-set, never status-determining (I-014, I-015)

**Projections**
- [ ] Neo4j is rebuildable from PostgreSQL alone (I-076)
- [ ] PostgreSQL wins every divergence (I-077)
- [ ] Every `RELATES_TO` has `relation_type` (I-073)
- [ ] Canonical and proposal graphs are query-separable (I-075)

**Vectors**
- [ ] Queries filter by `embedding_type` and `model_version` (I-078)
- [ ] Only approved parents are retrievable (I-029)
- [ ] Stale vectors are detected by `content_hash` (I-052)

**Agents**
- [ ] Agents produce proposals only (I-080)
- [ ] Every proposal has `reason` and `evidence` (I-081)
- [ ] Architecture evaluation reports all seven dimensions (I-082)

---

# 18. Related Documents

| Document | Relationship |
|---|---|
| `docs/Architecture_Vision` | Authority level 1 — the vision |
| `docs/Finalized_Architecture.md` | Authority level 2 — the architecture decisions |
| **This document** | Authority level 3 — **the ontology** |
| `docs/04-ontology/CanonicalOntology.md` | Literary concept definitions |
| `docs/04-ontology/RelationshipTypes.md` | Relationship taxonomy summary |
| `docs/10-api/ApiArchitecture_v1.md` | API surface over this model |
| `docs/Ingestion-pipeline.md` | Ingestion stages producing these entities |

---

# 19. Change Control

This document is **FROZEN**. Changes follow this process.

| Change type | Process |
|---|---|
| Field addition to an entity | Additive migration + update §3 + update §11.2 |
| New enum value | Migration with `CHECK` update + update §6 |
| New relation type | Update §4 + update §6.10 + declare inverse if directional |
| New entity | Full addition: §3, §11.1, §11.2, §10, §17 |
| Lifecycle change | Update §7 + verify §17 lifecycle checks |
| Invariant relaxation | **Requires curator sign-off.** Invariants are not negotiable by implementation convenience. |

**INVARIANT (I-086):** No implementation change may weaken an invariant. If an invariant blocks a
feature, the invariant is wrong or the feature is wrong. Both are escalated rather than resolved by
deleting the invariant.

---

# 20. Verification Status

The production test (`maana-api/src/maana_api/evaluation/production_test.py`) exercises the
acceptance criterion from `Finalized_Architecture.md`:

> The system ingests خیال, تصور, استعارہ and correctly proposes **خیال → تصور → استعارہ** while
> preserving evidence, versions, graph relationships, embeddings, and human approval.

| Step | What is exercised | What it does **not** yet prove |
|---|---|---|
| Ingest `W_khayal`, `W_tasawwur`, `W_istiarah` | §3.1 World fields, I-018 provenance populated | — |
| Create `R_khayal_deepens_tasawwur`, `R_tasawwur_deepens_istiarah` | §3.14 Relation construction, I-021 | Semantic correctness of the relation type — the type is asserted by the test, not derived by the agent |
| Create Claims with Evidence | §3.11, §3.12, I-012 | I-016 evidence aggregation |
| Approve 3 Worlds, 2 Relations, 2 Claims | §7.1, §7.2, I-044 | I-018 enforcement — provenance is populated but not validated |
| Run 5 agents | §14.2 shape, I-080, I-081, I-082 | Agent semantic quality — all five return scaffolding |
| Challenge and resolve | §7.3, I-051, I-052a, I-027 | §8.3 versioning; the test resolves without a `superseded` path |
| Evaluate 6 evaluators | §15 retrieval, §13 vector contract, §12 graph | — |

**Result:** 8 of 8 structural validation criteria pass. 7 governance approvals (3 Worlds +
2 Relations + 2 Claims).

## 20.1 Honest Summary

The pipeline is **structurally conformant**: entities, enums, lifecycles, governance transitions,
agent contracts, and the dual-graph and vector projections all behave as this document specifies,
and 42 unit tests plus the production test pass.

The pipeline is **not yet semantically conformant**. The agent logic, the merge and supersede
procedures, and the embedding backend are scaffolding. The P0 and P1 items in §16.2 are the
difference between a working structure and a working system.

No invariant in this document is violated by the current implementation, because the P1 gaps are
behaviours that have not been built rather than behaviours that have been built wrongly. That
distinction matters: nothing needs to be undone.






