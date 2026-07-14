# Ma'na Editorial Workflow And Versioning v1

## Purpose

This document defines how Ma'na should govern the lifecycle of knowledge objects.

It does not define interface screens, API endpoints, or database tables.

Its purpose is to establish how claims, ontology entities, mappings, relationships, and commentary artifacts should move through:

- creation
- proposal
- review
- approval
- dispute
- revision
- deprecation
- restoration

This document exists because Ma'na cannot rely on schema quality alone.

Even a strong domain model will fail if the editorial workflow allows:

- silent authority
- irreversible mistakes
- provenance loss
- hidden AI influence
- ontology drift
- approval without scope

## Foundational Principle

In Ma'na, governance is part of knowledge itself.

How a claim was created, reviewed, approved, challenged, revised, and possibly deprecated is not peripheral metadata.

It is part of what gives that claim its trustworthiness and usable status.

## Governance Objects

This workflow applies, with different intensity, to the following object families:

- claims
- ontology entities
- ontology mappings
- relationships
- commentary artifacts
- question objects
- cross-reference links

Not all objects require the same review depth, but all meaningful objects must be governable.

## Governance Principles

## 1. No Silent Canonicalization

No object becomes canonical merely because it exists, appears persuasive, or has been reused repeatedly.

## 2. Approval Requires Scope

Approvals must always answer:

- approved for what
- approved by whom
- approved under which framework
- approved at what level

## 3. Reversibility Is Mandatory

Every meaningful approval must be reversible.

The system must always be able to answer:

- why this was approved
- what evidence supported it
- what object it replaced
- who approved it
- what changed afterward

## 4. AI Assistance Must Remain Visible

If AI contributed materially to a knowledge object or review recommendation, that involvement must remain auditable.

## 5. Disagreement Must Remain Representable

The workflow must allow disagreement to persist without forcing premature closure.

## 6. Governance Should Match Downstream Impact

The stronger the downstream consequences of an object, the stricter the governance threshold.

## Governance Roles

The model does not prescribe an organization chart, but it does require distinct governance roles.

## 1. Contributor

Produces candidate objects.

### Examples

- scholar
- editor
- translator
- reader
- AI system
- ingestion pipeline

## 2. Reviewer

Evaluates candidate objects for sufficiency, coherence, and evidentiary support.

## 3. Curator

Makes governance decisions that affect reuse, canonicality, ontology stability, and public presentation.

## 4. Maintainer

Preserves continuity across versions, deprecations, merges, restorations, and audit history.

## 5. System Agent

An automated process that may propose, classify, cluster, compare, or pre-validate objects, but does not hold ultimate authority.

## Governance Levels

Different objects should move through different levels of governance.

## 1. Private Or Working Level

Used for drafts, notes, temporary AI outputs, experimental mappings, or incomplete review material.

### Characteristics

- low visibility
- reversible without ceremony
- not canonical
- may be incomplete

## 2. Editorial Level

Used for internally reviewed artifacts that are stable enough for team use but not yet treated as broad reusable truth.

### Characteristics

- reviewed
- scoped
- reusable within editorial workflows
- still revisable

## 3. Canonical Level

Used only for objects stable enough for system-wide reuse.

### Characteristics

- explicit approval
- strong provenance
- auditable evidence or rationale
- stable reference identity
- visible scope

## Object-Specific Review Thresholds

## 1. Claims

Claims may exist at draft level, but high-impact claims require review before reuse.

### High-Impact Claim Examples

- ontology mappings
- public-facing interpretive claims
- cross-work comparisons
- graph-forming relation claims

## 2. Ontology Entities

Ontology proposals should face stronger review than ordinary commentary drafts because they affect the entire corpus.

## 3. Ontology Mappings

Mappings should be reviewed more strictly than local notes because they shape retrieval and graph structure.

## 4. Commentary Artifacts

Commentary may be drafted quickly, but canonical commentary requires stronger review because it becomes a public explanatory layer.

## 5. AI-Derived Objects

AI-generated proposals should always begin below canonical level unless explicitly reviewed and elevated.

## Lifecycle States

The workflow should support the following conceptual states.

Not every object needs every state, but the system must support them where relevant.

## 1. Draft

The object exists but has not yet been proposed for review.

### Typical Use

- working notes
- AI proposals
- incomplete interpretations
- rough mappings

## 2. Proposed

The object has been submitted into a governance process.

### Requirements

- object identity
- scope
- contributor identity or class
- minimum provenance

## 3. In Review

The object is actively undergoing evaluation.

### Possible Activities

- evidence check
- provenance check
- ontology duplicate check
- comparison to prior versions
- disagreement review

## 4. Reviewed

The object has completed a review pass, but may not yet be approved for canonical use.

## 5. Approved

The object has been accepted for defined reuse.

### Rule

Approval is always scoped.

## 6. Contested

The object remains active but has an open challenge.

This state is important because knowledge should not disappear merely because it is under dispute.

## 7. Rejected

The object was reviewed and not accepted for its proposed role.

Rejected does not require deletion.

It may still remain in history for audit and learning.

## 8. Deprecated

The object was previously approved or canonical but is no longer preferred.

### Important

Deprecation is not erasure.

It must preserve traceability.

## 9. Superseded

The object has been replaced by a newer object or version that should now be preferred.

## 10. Restored

A previously rejected or deprecated object has been reactivated under explicit governance.

## Editorial Actions

The governance model should support explicit actions rather than hidden mutation.

## 1. Approve

Elevates an object for scoped reuse.

## 2. Reject

Declines the object for the proposed role.

## 3. Request Revision

Returns the object for further work without rejecting its underlying direction.

## 4. Merge

Combines overlapping entities or records under a governed decision.

This is especially important for ontology.

## 5. Split

Separates an overly broad or conflated object into multiple governed objects.

## 6. Rename

Changes preferred label without destroying history.

## 7. Alias

Preserves alternate labels without multiplying entities.

## 8. Deprecate

Marks an object as no longer preferred while retaining backward traceability.

## 9. Restore

Reactivates a previously deprecated or rejected object under explicit rationale.

## 10. Supersede

Replaces an object with another while preserving lineage.

## Approval Scope Model

Approval in Ma'na must always carry explicit scope.

Possible scopes include:

- for this work
- for this witness
- for this unit
- for this tradition
- for this language
- for this editorial house
- for system-wide canonical registry

### Rule

The wider the scope, the stronger the review burden.

## Versioning Principles

Versioning is required because scholarship evolves, AI outputs improve, and curator judgment changes over time.

## 1. No Destructive Overwrite

Meaningful objects should not be replaced by silent mutation.

They should evolve through visible versioning or linked revision lineage.

## 2. Stable Identity, Evolving State

An object may retain stable identity across revisions, but the system must preserve what changed between versions.

## 3. Major Versus Minor Change

Ma'na should conceptually distinguish:

- small editorial cleanup
- evidence expansion
- interpretive revision
- scope change
- canonicality change
- ontology remapping

Not every change carries equal epistemic weight.

## 4. Version Lineage

Every meaningful revision should preserve:

- prior version reference
- editor or agent of change
- change rationale
- evidence delta where relevant
- status delta where relevant

## 5. Public Preference Versus Historical Record

The system may prefer one current version for public use while still preserving all prior governed versions.

## Versioning By Object Family

## 1. Claim Versioning

Claims should version when:

- wording materially changes meaning
- evidence basis changes
- scope changes
- truth status changes
- provenance is corrected in a meaningful way

## 2. Ontology Entity Versioning

Ontology entities should version more conservatively, but governance actions must remain visible:

- rename
- merge
- split
- alias
- deprecate
- restore

## 3. Commentary Versioning

Commentary should version when:

- core explanation changes materially
- new interpretive sections are added
- disagreement handling changes
- ontology links change meaningfully
- evidence basis changes
- AI-generated sections are replaced or approved

## 4. Mapping Versioning

Mappings should version when:

- the target entity changes
- support strength changes
- scope changes
- the mapping moves from inferred to approved

## Evidence And Review Requirements

The workflow should not demand identical evidence from every object, but it must require sufficiency proportional to impact.

## Low-Impact Objects

May require:

- basic provenance
- clear scope
- minimal review

## High-Impact Objects

Should require:

- stronger evidence
- explicit rationale
- reviewer or curator attribution
- duplicate/conflict checks
- version traceability

## Disagreement Workflow

Disagreement is not an exception path.

It is part of the ordinary lifecycle of knowledge in Ma'na.

## 1. Supported Multiplicity

The system must allow multiple approved interpretations to coexist when their scope or tradition differs.

## 2. Contested State

An object may remain usable while explicitly marked contested.

## 3. Counter-Claim Support

The workflow should allow an object to be challenged by another addressable object rather than only by informal notes.

## 4. No Premature Resolution

Curators should not be forced to collapse every dispute into one winner if the corpus is better served by visible plurality.

## AI In The Editorial Workflow

## 1. Permitted AI Workflow Functions

AI may assist with:

- candidate extraction
- duplicate detection
- evidence clustering
- ontology suggestion
- conflict surfacing
- revision suggestion
- summary drafting

## 2. AI Review Limits

AI may recommend governance actions but must not finalize them autonomously for high-impact objects.

## 3. AI Provenance Requirement

Whenever AI materially shaped:

- a claim
- a mapping
- a commentary section
- a merge recommendation
- a deprecation recommendation

that involvement should remain recoverable in review history.

## Canonical Registry Workflow

Ontology governance requires a stricter workflow because ontology decisions affect the whole corpus.

## Suggested Lifecycle

1. Proposed candidate entity
2. Duplicate and alias check
3. Scope and definition review
4. Curator decision
5. Approval, merge, split, rename, alias, reject, or deprecate
6. Registry history preservation

## Rule

No AI-generated ontology candidate should enter canonical registry status without explicit human governance.

## Commentary Workflow

Commentary should move through a workflow that protects both quality and plurality.

## Suggested Lifecycle

1. Draft commentary artifact
2. Scope and source anchoring check
3. Claim and evidence review
4. Provenance and AI involvement review
5. Ontology link review
6. Disagreement visibility review
7. Approval for defined use

### Possible Approval Targets

- internal editorial use
- public reader use
- tradition-specific use
- canonical house commentary

## Audit Principles

Audit history is not optional in Ma'na.

The system should always preserve enough history to answer:

- who changed this
- why it changed
- what changed
- what evidence or rationale supported the change
- what status it had before
- whether AI contributed

## Forbidden Workflow Patterns

Any future implementation violates this model if it allows:

- silent overwrite of approved objects
- automatic canonicalization of AI proposals
- loss of deprecated history
- approval with no visible scope
- ontology merges with no lineage
- commentary revisions with no provenance delta
- disputes being hidden for cleaner presentation

## Practical Consequence

This workflow model implies that Ma'na will need, eventually:

- reviewable object histories
- reversible governance actions
- visible scope on approvals
- audit trails for AI assistance
- distinct status layers for editorial state and epistemic state

This document does not define how those are implemented.

It defines that they must exist.

## Next Best Step

The next architecture artifact should be:

`RetrievalAndStorageArchitecture_v1.md`

That document should explain how these governed objects should be represented across:

- relational structures
- document artifacts
- vector retrieval
- graph traversal
- preserved source storage

without collapsing the conceptual boundaries established by the earlier documents.
