# Ma'na API Architecture v1

## Purpose

This document defines the API contracts for Ma'na Phase 6.

It is implementation-facing. All endpoints, request/response schemas, and error codes are defined here.

This document must not redefine ontology concepts.

## Base URL

```
/api/v1
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <token>
```

Service-to-service communication uses API keys:

```
X-API-Key: <key>
```

## Standard Response Format

### Success

```json
{
  "data": {},
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

### Error

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

## Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| CONFLICT | 409 | State conflict (e.g., duplicate proposal) |
| UNPROCESSABLE | 422 | Business rule violation |
| INTERNAL_ERROR | 500 | Server error |

## Pagination

List endpoints support pagination:

```
GET /api/v1/claims?page=1&page_size=20
```

Response:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5
  }
}
```

## Filtering and Sorting

List endpoints support filtering and sorting:

```
GET /api/v1/claims?status=approved&unit_id=123&sort=-created_at
```

## Ingestion Endpoints

### Start Ingestion

```http
POST /ingest/url
```

Request:

```json
{
  "url": "https://youtu.be/example",
  "source_type": "lecture",
  "language": "ur",
  "options": {
    "transcribe": true,
    "annotate": true,
    "extract_vocabulary": true
  }
}
```

Response:

```json
{
  "data": {
    "job_id": "uuid",
    "status": "queued",
    "created_at": "ISO8601"
  }
}
```

### Start Ingestion from File

```http
POST /ingest/file
```

Request: multipart/form-data with file and metadata.

### Get Ingestion Status

```http
GET /ingest/{job_id}/status
```

Response:

```json
{
  "data": {
    "job_id": "uuid",
    "status": "processing",
    "current_stage": "transcription",
    "progress": 0.45,
    "stages": [
      {"name": "download", "status": "completed"},
      {"name": "transcription", "status": "processing"},
      {"name": "cleaning", "status": "pending"},
      {"name": "annotation", "status": "pending"}
    ]
  }
}
```

### Get Ingestion Artifacts

```http
GET /ingest/{job_id}/artifacts
```

Response:

```json
{
  "data": {
    "job_id": "uuid",
    "artifacts": [
      {
        "kind": "raw_audio",
        "uri": "minio://raw-sources/lectures/abc/original.mp3",
        "size_bytes": 12345678,
        "created_at": "ISO8601"
      },
      {
        "kind": "transcript",
        "uri": "minio://transcripts/lectures/abc/transcript.json",
        "size_bytes": 123456,
        "created_at": "ISO8601"
      }
    ]
  }
}
```

## Claim Endpoints

### Create Claim Candidate

```http
POST /claims
```

Request:

```json
{
  "type": "interpretive",
  "scope": {
    "unit_id": "uuid",
    "work_id": "uuid"
  },
  "content": "This couplet evokes the experience of longing mixed with resignation.",
  "evidence_anchors": [
    {
      "type": "textual_span",
      "source_ref": "minio://transcripts/lectures/abc/transcript.json",
      "span": {"start": 120.5, "end": 125.3},
      "text": " quoted passage here "
    }
  ],
  "proposed_ontology_mappings": [
    {"entity_type": "human_experience", "entity_name": "Longing", "confidence": 0.9}
  ],
  "tradition": "Sufi commentary",
  "source_language": "ur"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "type": "interpretive",
    "status": "proposed",
    "content": "...",
    "evidence_anchors": [...],
    "provenance": {
      "contributor_id": "uuid",
      "contributor_type": "ai_system",
      "method": "llm_extraction",
      "timestamp": "ISO8601",
      "model": "gpt-4o"
    },
    "created_at": "ISO8601"
  }
}
```

### Get Claim

```http
GET /claims/{claim_id}
```

### Get Claims for Unit

```http
GET /claims?unit_id={unit_id}&status=approved
```

### Attach Evidence

```http
POST /claims/{claim_id}/evidence
```

Request:

```json
{
  "type": "textual_span",
  "source_ref": "minio://...",
  "span": {"start": 120.5, "end": 125.3},
  "text": "..."
}
```

## Ontology Endpoints

### Search Canonical Registry

```http
GET /ontology/search?q={query}&type={entity_type}&language={lang}
```

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "type": "human_experience",
      "name": "Longing",
      "aliases": ["شوق", "انتظار"],
      "description": "...",
      "language": "en",
      "is_canonical": true,
      "usage_count": 42
    }
  ]
}
```

### Propose New Ontology Entity

```http
POST /ontology/propose
```

Request:

```json
{
  "entity_type": "symbol",
  "name": "Mirror",
  "aliases": ["آئینه", "مرآة"],
  "description": "A symbol of self-consciousness and reflection.",
  "proposed_mappings": [
    {"concept": "Selfhood", "confidence": 0.8}
  ],
  "evidence": [
    {
      "type": "textual_span",
      "source_ref": "...",
      "text": "..."
    }
  ]
}
```

### Approve Proposal

```http
POST /ontology/{proposal_id}/approve
```

Request:

```json
{
  "decision_notes": "Approved after review of three instances.",
  "merge_with_existing": null
}
```

### Merge Proposal

```http
POST /ontology/{proposal_id}/merge
```

Request:

```json
{
  "target_entity_id": "uuid",
  "decision_notes": "Merged with existing 'Longing' entity."
}
```

## Review Endpoints

### Get Review Queue

```http
GET /review/queue?type=ontology&status=pending&page=1&page_size=20
```

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "type": "ontology_proposal",
      "status": "pending",
      "created_at": "ISO8601",
      "proposal": {
        "entity_type": "symbol",
        "name": "Mirror"
      },
      "evidence_summary": "3 textual spans",
      "contributor": {
        "type": "ai_system",
        "name": "extraction-pipeline-v2"
      }
    }
  ],
  "pagination": {...}
}
```

### Approve Review Item

```http
POST /review/{item_id}/approve
```

### Reject Review Item

```http
POST /review/{item_id}/reject
```

Request:

```json
{
  "reason": "Insufficient evidence across traditions."
}
```

### Get Decision History

```http
GET /review/decisions?entity_id={entity_id}
```

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "action": "approved",
      "timestamp": "ISO8601",
      "reviewer_id": "uuid",
      "notes": "Approved after review."
    }
  ]
}
```

## Commentary Endpoints

### Compose Commentary

```http
POST /commentary/compose
```

Request:

```json
{
  "scope": {
    "type": "unit",
    "id": "uuid"
  },
  "approved_claim_ids": ["uuid", "uuid"],
  "options": {
    "include_evidence": true,
    "include_provenance": true,
    "include_uncertainty": true
  }
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "status": "draft",
    "content": "# Commentary\n\n...",
    "linked_claims": ["uuid"],
    "provenance": {
      "composed_at": "ISO8601",
      "composed_by": "commentary-service",
      "source_claims": ["uuid"]
    }
  }
}
```

### Get Commentary

```http
GET /commentary/{commentary_id}
```

### Get Commentary Claims

```http
GET /commentary/{commentary_id}/claims
```

### Publish Commentary

```http
POST /commentary/{commentary_id}/publish
```

## Retrieval Endpoints

### Source Retrieval

```http
POST /retrieve/source
```

Request:

```json
{
  "query": {
    "type": "unit",
    "id": "uuid"
  }
}
```

Response:

```json
{
  "data": {
    "source": {
      "witness": {...},
      "segment": {
        "text": "...",
        "span": {"start": 120.5, "end": 125.3},
        "source_ref": "minio://..."
      }
    }
  }
}
```

### Commentary Retrieval

```http
POST /retrieve/commentary
```

Request:

```json
{
  "query": {
    "type": "unit",
    "id": "uuid"
  },
  "filters": {
    "status": "approved",
    "tradition": "Sufi commentary"
  }
}
```

### Ontology Retrieval

```http
POST /retrieve/ontology
```

Request:

```json
{
  "query": {
    "entity_type": "human_experience",
    "name": "Longing"
  }
}
```

Response:

```json
{
  "data": {
    "entity": {
      "id": "uuid",
      "type": "human_experience",
      "name": "Longing"
    },
    "related_units": [
      {"unit_id": "uuid", "work_title": "...", "relevance": 0.95}
    ]
  }
}
```

### Graph Retrieval

```http
POST /retrieve/graph
```

Request:

```json
{
  "query": {
    "start_entity_id": "uuid",
    "relation_types": ["EVOKES", "RELATES_TO"],
    "depth": 2
  }
}
```

### Semantic Retrieval

```http
POST /retrieve/semantic
```

Request:

```json
{
  "query": "I feel lonely after success",
  "filters": {
    "content_types": ["commentary", "source_segment"],
    "status": "approved"
  },
  "limit": 10
}
```

Response:

```json
{
  "data": {
    "results": [
      {
        "id": "uuid",
        "type": "commentary",
        "score": 0.92,
        "snippet": "...",
        "source_anchor": {
          "unit_id": "uuid",
          "work_title": "..."
        },
        "ontology_links": [
          {"entity_type": "human_experience", "name": "Loneliness"}
        ]
      }
    ]
  }
}
```

### Composed Retrieval

```http
POST /retrieve/compose
```

Request:

```json
{
  "query": "Why does God feel absent in Ghalib?",
  "layers": ["semantic", "ontology", "graph", "commentary", "source"]
}
```

Response:

```json
{
  "data": {
    "semantic_results": [...],
    "ontology_entities": [...],
    "graph_expansion": [...],
    "commentary": [...],
    "source_evidence": [...]
  }
}
```

## Health and Status

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "graph": "healthy",
    "vector": "healthy",
    "storage": "healthy"
  }
}
```

### Readiness Check

```http
GET /ready
```

Response:

```json
{
  "ready": true,
  "checks": {
    "database_migrations": "up_to_date",
    "canonical_registry": "loaded",
    "curator_workflow": "active"
  }
}
```

## Versioning

- All endpoints are prefixed with `/api/v1`
- Breaking changes require a new version
- Non-breaking changes are backward compatible
- Deprecated endpoints return a `Deprecation` header with sunset date

## Rate Limiting

- Authenticated users: 1000 requests/minute
- Service accounts: 10000 requests/minute
- Rate limit headers included in all responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

## Idempotency

All mutation endpoints support idempotency keys:

```
Idempotency-Key: <uuid>
```

Retrying with the same idempotency key returns the same result without duplicate processing.

## Semantic Engine Endpoints

### World CRUD

```http
POST /worlds
```

Request:

```json
{
  "canonical_term": "خیال",
  "transliteration": "Khayal",
  "persian_term": "خیال",
  "urdu_term": "خیال",
  "arabic_root": "خ ي ل",
  "english_gloss": "Imagination",
  "short_definition": "...",
  "literal_meaning": "...",
  "expanded_meaning": "...",
  "central_question": "...",
  "central_axis": "...",
  "semantic_dimensions": {
    "quranic": "...",
    "philosophical": "...",
    "literary": "...",
    "modern": "..."
  },
  "chapter_id": "uuid",
  "cluster_id": "uuid",
  "proposed_relations": [
    {"target_world_id": "uuid", "type": "PRECEDES", "confidence": 0.9}
  ]
}
```

### Get World

```http
GET /worlds/{world_id}
```

### Get Related Worlds

```http
GET /worlds/{world_id}/related
```

### Get Semantic Paths

```http
GET /worlds/{world_id}/path
```

### Get Graph Neighborhood

```http
GET /worlds/{world_id}/graph
```

### Chapter Endpoints

```http
GET /chapters/{chapter_id}
GET /chapters/{chapter_id}/architecture
```

### Semantic Analysis

```http
POST /semantic/analyze
```

Request:

```json
{
  "world_id": "uuid",
  "analysis_type": "full"
}
```

### Propose Relations

```http
POST /semantic/propose-relations
```

Request:

```json
{
  "source_world_id": "uuid",
  "candidates": ["uuid", "uuid"],
  "relation_types": ["PRECEDES", "DEEPENS", "RELATED_TO"]
}
```

### Review Semantic Proposals

```http
POST /semantic/review
```

Request:

```json
{
  "proposal_id": "uuid",
  "action": "approve",
  "notes": "..."
}
```

### Get Gaps

```http
GET /gaps
```

Response:

```json
{
  "data": [
    {
      "type": "graph_hole",
      "description": "Missing bridge between خیال and عشق",
      "confidence": 0.8
    }
  ]
}
```

### Get Architecture Proposals

```http
GET /architecture/proposals
```

### Get Architecture History

```http
GET /architecture/history?world_id={world_id}
```

### Run Architect Agent

```http
POST /worlds/{world_id}/architect
```

Response:

```json
{
  "data": {
    "world_id": "uuid",
    "recommended_chapter": "CH09",
    "recommended_cluster": "Imagination",
    "relationships": [],
    "architectural_changes": [],
    "potential_reordering": [],
    "new_cluster_required": false,
    "confidence": 0.87
  }
}
```

## Semantic Projection Events

The following events are emitted by the Semantic Projection Service:

- `WORLD_CREATED`
- `WORLD_UPDATED`
- `WORLD_RELATION_CHANGED`
- `WORLD_DELETED`

Consumers may subscribe to these events for cache invalidation, index updates, and downstream notifications.
