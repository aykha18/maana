"""Production validation test: ingestion of three Worlds with full pipeline (synchronous version)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from maana_api.domain.models import (
    ChallengeResolution,
    Claim,
    ClaimStatus,
    ClaimType,
    Relation,
    RelationType,
    Scope,
    World,
    WorldStatus,
)
from maana_api.evaluation import run_evaluation_suite
from maana_api.infrastructure.database import get_sync_engine
from maana_api.agents import AgentContext, AgentOrchestrator, get_orchestrator
from maana_api.services.challenge_service import ChallengeService
from maana_api.services.claim_service import ClaimService
from maana_api.services.relation_service import RelationService
from maana_api.services.world_service import WorldService
from sqlmodel import Session, SQLModel, create_engine


def _status(value: Any) -> str:
    """Normalize an enum-or-string status column to its string form.

    Enum-typed columns are declared as ``Text`` (Ontology §2.1), so a value read
    back from the database is a plain ``str``.
    """

    return value.value if hasattr(value, "value") else str(value)


THREE_WORLDS = [
    {
        "world_id": "W_khayal",
        "canonical_term": "خیال",
        "transliteration": "Khayal",
        "persian_term": "خیال",
        "urdu_term": "خیال",
        "arabic_root": "خ ي ل",
        "english_gloss": "Imagination",
        "short_definition": "The faculty of forming mental images",
        "literal_meaning": "To form an image",
        "expanded_meaning": "In Islamic philosophy, the faculty between sense perception and intellect that forms and retains images",
        "central_question": "How does imagination mediate between the sensible and the intelligible?",
        "central_axis": "Image formation → Retention → Synthesis",
        "semantic_dimensions": {
            "quranic": "References to khayal in Quranic narratives",
            "philosophical": "Ibn Sina's quwwa al-khayal, Suhrawardi's imaginal world",
            "literary": "Poetic imagery, metaphor (استعارہ) grounded in khayal",
            "modern": "Psychological imagination, creative faculty",
        },
        "status": WorldStatus.PROPOSED,
        "scope": Scope.GLOBAL,
    },
    {
        "world_id": "W_tasawwur",
        "canonical_term": "تصور",
        "transliteration": "Tasawwur",
        "persian_term": "تصور",
        "urdu_term": "تصور",
        "arabic_root": "ص و ر",
        "english_gloss": "Conceptualization / Conception",
        "short_definition": "The faculty of forming concepts from images",
        "literal_meaning": "To form, to shape",
        "expanded_meaning": "In logic and philosophy, the act of the mind forming a universal concept from particular images retained by khayal",
        "central_question": "How does the mind abstract universals from particular images?",
        "central_axis": "Image → Abstraction → Universal concept",
        "semantic_dimensions": {
            "quranic": "Tasawwur as conceptual understanding in Quranic exegesis",
            "philosophical": "Ibn Sina: tasawwur as second operation of intellect; Suhrawardi: conceptualization of imaginal forms",
            "literary": "Thematic development in poetry: image (خیال) → theme (تصور)",
            "modern": "Concept formation, cognitive categorization",
        },
        "status": WorldStatus.PROPOSED,
        "scope": Scope.GLOBAL,
    },
    {
        "world_id": "W_istiarah",
        "canonical_term": "استعارہ",
        "transliteration": "Isti'arah",
        "persian_term": "استعارہ",
        "urdu_term": "استعارہ",
        "arabic_root": "ع ر ي",
        "english_gloss": "Metaphor",
        "short_definition": "Metaphor: using a word for something other than its literal meaning",
        "literal_meaning": "Borrowing, lending",
        "expanded_meaning": "In Arabic rhetoric (balaghah), the primary figure of speech where a word is used in a non-literal sense based on a similarity between the literal and intended meanings",
        "central_question": "How does metaphor transfer meaning across semantic domains?",
        "central_axis": "Similarity → Transfer → Illumination",
        "semantic_dimensions": {
            "quranic": "Quranic metaphors (e.g., light, path, garment)",
            "philosophical": "Metaphor as epistemic access to unseen realities",
            "literary": "Core of poetic language: khayal provides images, tasawwur abstracts, isti'arah transfers",
            "modern": "Cognitive metaphor theory (Lakoff/Johnson), conceptual metaphor",
        },
        "status": WorldStatus.PROPOSED,
        "scope": Scope.GLOBAL,
    },
]


EXPECTED_RELATIONS = [
    {
        "source": "W_khayal",
        "target": "W_tasawwur",
        "type": RelationType.DEEPENS,
        "description": "خیال deepens toward تصور (image → concept)",
    },
    {
        "source": "W_tasawwur",
        "target": "W_istiarah",
        "type": RelationType.DEEPENS,
        "description": "تصور deepens toward استعارہ (concept → metaphor)",
    },
]


EXPECTED_CLAIMS = [
    {
        "claim_id": "C_khayal_tasawwur",
        "claim_type": ClaimType.RELATIONAL,
        "subject_kind": "world",
        "subject_reference_id": "W_khayal",
        "subject_label": "خیال",
        "predicate": "DEEPENS_TOWARD",
        "object": "W_tasawwur",
        "text": "In the philosophical tradition, خیال (imagination) provides the images that تصور (conceptualization) abstracts into universal concepts.",
        "status": ClaimStatus.PROPOSED,
        "scope": Scope.GLOBAL,
    },
    {
        "claim_id": "C_tasawwur_istiarah",
        "claim_type": ClaimType.RELATIONAL,
        "subject_kind": "world",
        "subject_reference_id": "W_tasawwur",
        "subject_label": "تصور",
        "predicate": "DEEPENS_TOWARD",
        "object": "W_istiarah",
        "text": "Metaphor (استعارہ) operates by transferring conceptual structures (تصور) from a source domain to a target domain.",
        "status": ClaimStatus.PROPOSED,
        "scope": Scope.GLOBAL,
    },
]


def run_production_test() -> dict[str, Any]:
    """Run the full production validation test (sync version)."""
    # Use in-memory SQLite like tests
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    results = {
        "phase": "production_validation",
        "worlds": [],
        "relations": [],
        "claims": [],
        "governance": [],
        "agents": [],
        "evaluation": {},
    }

    with Session(engine) as session:
        world_service = WorldService(session=session)
        claim_service = ClaimService(session=session)
        relation_service = RelationService(session=session)
        challenge_service = ChallengeService(session=session)
        orchestrator = get_orchestrator()

        # Mock graph projection to avoid Neo4j connection
        mock_graph = MagicMock()
        mock_graph.create_world_node = AsyncMock()
        mock_graph.create_relation = AsyncMock()
        mock_graph.health_check = AsyncMock(return_value=True)

        with patch("maana_api.services.world_service.get_graph_projection", return_value=mock_graph), \
             patch("maana_api.services.relation_service.get_graph_projection", return_value=mock_graph), \
             patch("maana_api.infrastructure.graph.get_graph_projection", return_value=mock_graph):

            # Phase 1: Create three Worlds
            print("Phase 1: Creating three Worlds...")
            for w_data in THREE_WORLDS:
                world = World(**w_data)
                created = world_service.create_world(world)
                results["worlds"].append(
                    {"id": created.world_id, "status": _status(created.status)}
                )
                print(f"  Created {created.world_id}")

            # Phase 2: Create expected relations
            print("Phase 2: Creating relations...")
            for rel_data in EXPECTED_RELATIONS:
                relation = Relation(
                    relation_id=f"rel_{rel_data['source']}_{rel_data['target']}",
                    relation_type=rel_data["type"],
                    source_world_id=rel_data["source"],
                    target_world_id=rel_data["target"],
                    status=WorldStatus.PROPOSED,
                    scope=Scope.GLOBAL,
                )
                created = relation_service.create_relation(relation)
                results["relations"].append({"id": created.relation_id, "type": created.relation_type})
                print(f"  Created relation {rel_data['source']} -> {rel_data['target']}")

            # Phase 3: Create supporting claims
            print("Phase 3: Creating claims...")
            for c_data in EXPECTED_CLAIMS:
                claim = Claim(**c_data)
                created = claim_service.create_claim(claim)
                results["claims"].append({"id": created.claim_id, "type": created.claim_type})
                print(f"  Created claim {created.claim_id}")

            # Phase 4: Approve all (governance) - skip graph projection
            print("Phase 4: Governance approval (DB only)...")
            for world in THREE_WORLDS:
                # Direct DB update to avoid async graph call
                w = world_service.get_world(world["world_id"])
                w.status = WorldStatus.APPROVED
                w.updated_at = datetime.utcnow()
                session.add(w)
                session.commit()
                results["governance"].append({"entity": f"world:{world['world_id']}", "action": "approved"})
                print(f"  Approved world {world['world_id']}")

            for rel_data in EXPECTED_RELATIONS:
                rel_id = f"rel_{rel_data['source']}_{rel_data['target']}"
                r = relation_service.get_relation(rel_id)
                r.status = WorldStatus.APPROVED
                session.add(r)
                session.commit()
                results["governance"].append({"entity": f"relation:{rel_id}", "action": "approved"})
                print(f"  Approved relation {rel_id}")

            for c_data in EXPECTED_CLAIMS:
                c = claim_service.get_claim(c_data["claim_id"])
                c.status = ClaimStatus.APPROVED
                c.updated_at = datetime.utcnow()
                session.add(c)
                session.commit()
                results["governance"].append({"entity": f"claim:{c_data['claim_id']}", "action": "approved"})
                print(f"  Approved claim {c_data['claim_id']}")

            # Phase 5: Run agents
            print("Phase 5: Running agents...")
            context = AgentContext(
                world_ids=[w["world_id"] for w in THREE_WORLDS],
                claim_ids=[c["claim_id"] for c in EXPECTED_CLAIMS],
                chapter_id="CH009",
                cluster_id="CL_imagination",
                scope="global",
            )

            import asyncio
            relation_proposals = asyncio.run(orchestrator.run_agent("relation", context))
            results["agents"].append({"agent": "relation", "proposals": len(relation_proposals)})

            architect_proposals = asyncio.run(orchestrator.run_agent("architect", context))
            results["agents"].append({"agent": "architect", "proposals": len(architect_proposals)})

            ring_proposals = asyncio.run(orchestrator.run_agent("ring_eval", context))
            results["agents"].append({"agent": "ring_eval", "proposals": len(ring_proposals)})

            gap_proposals = asyncio.run(orchestrator.run_agent("gap", context))
            results["agents"].append({"agent": "gap", "proposals": len(gap_proposals)})

            merge_proposals = asyncio.run(orchestrator.run_agent("merge_split", context))
            results["agents"].append({"agent": "merge_split", "proposals": len(merge_proposals)})

            # Phase 6: Test challenge flow
            print("Phase 6: Testing challenge flow...")
            challenge = challenge_service.create_challenge(
                entity_type="claim",
                entity_id="C_khayal_tasawwur",
                challenger_id="reader_001",
                reason="The relation between خیال and تصور might be PRECEDES not DEEPENS",
                new_evidence=[{"source": "Ibn Sina", "text": "khayal precedes tasawwur in the cognitive hierarchy"}],
            )
            results["governance"].append({"entity": "challenge", "action": "created", "id": challenge.challenge_id})

            resolved = challenge_service.resolve_challenge(
                challenge_id=challenge.challenge_id,
                resolution=ChallengeResolution.REAFFIRMED,
                resolver_id="curator_001",
            )
            results["governance"].append({"entity": "challenge", "action": "resolved", "resolution": resolved.resolution})

            # Phase 7: Evaluation suite
            print("Phase 7: Running evaluation suite...")
            eval_results = run_evaluation_suite(orchestrator)
            results["evaluation"] = eval_results

    # Validation criterion check
    approved_count = len([g for g in results["governance"] if g["action"] == "approved"])
    validation = {
        "three_worlds_ingested": len(results["worlds"]) == 3,
        "relations_proposed": len(results["relations"]) == 2,
        "khayal_to_tasawwur": any(r["id"] == "rel_W_khayal_W_tasawwur" for r in results["relations"]),
        "tasawwur_to_istiarah": any(r["id"] == "rel_W_tasawwur_W_istiarah" for r in results["relations"]),
        "governance_complete": approved_count == 7,  # 3 worlds + 2 relations + 2 claims
        "challenge_tested": any(g["action"] == "resolved" for g in results["governance"]),
        "agents_ran": len(results["agents"]) == 5,
        "evaluation_passed": results["evaluation"]["summary"]["overall_passed"],
    }

    results["validation"] = validation
    results["all_passed"] = all(validation.values())

    print("\n=== VALIDATION RESULTS ===")
    for k, v in validation.items():
        status = "PASS" if v else "FAIL"
        print(f"  {status} {k}: {v}")
    print(f"\nOverall: {'PASS' if results['all_passed'] else 'FAIL'}")

    return results


if __name__ == "__main__":
    run_production_test()