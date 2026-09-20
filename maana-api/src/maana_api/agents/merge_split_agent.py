"""Merge/Split Agent: handles synonym/near-synonym resolution and World splitting."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from maana_api.agents.base import Agent, AgentContext, AgentProposal, AgentType
from maana_api.domain.models import WorldStatus, Scope


class MergeCandidate(BaseModel):
    """A merge proposal for two Worlds."""

    source_world_id: str
    target_world_id: str
    merge_type: str  # "SYNONYM", "NEAR_SYNONYM", "SUBSUME"
    confidence: float
    conflict_analysis: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []
    reasoning: str


class SplitCandidate(BaseModel):
    """A split proposal for a World."""

    world_id: str
    proposed_worlds: list[dict[str, Any]]  # Each has term, definition, dimension
    confidence: float
    evidence: list[dict[str, Any]] = []
    reasoning: str


class MergeSplitAgent(Agent[list[MergeCandidate | SplitCandidate]]):
    """Handles synonym/near-synonym resolution and World splitting."""

    def __init__(self) -> None:
        super().__init__(AgentType.MERGE_SPLIT)

    async def run(self, context: AgentContext) -> list[AgentProposal[list[MergeCandidate | SplitCandidate]]]:
        """Analyze Worlds for merge/split opportunities."""
        candidates: list[MergeCandidate | SplitCandidate] = []

        # Check for merge candidates
        merge_candidates = await self._detect_merges(context)
        candidates.extend(merge_candidates)

        # Check for split candidates
        split_candidates = await self._detect_splits(context)
        candidates.extend(split_candidates)

        if not candidates:
            return []

        proposal = self.create_proposal(
            payload=candidates,
            confidence=sum(c.confidence for c in candidates) / len(candidates),
            reasoning=f"Detected {len(merge_candidates)} merge and {len(split_candidates)} split candidates",
            evidence=[e for c in candidates for e in c.evidence],
        )
        return [proposal]

    async def _detect_merges(self, context: AgentContext) -> list[MergeCandidate]:
        """Detect synonym/near-synonym pairs."""
        # In production:
        # 1. Compare World embeddings (cosine similarity > 0.95 = synonym, 0.85-0.95 = near-synonym)
        # 2. Compare definitions, dimensions, claims
        # 3. Check for claim conflicts
        # 4. Present to human for review

        # Placeholder
        return [
            MergeCandidate(
                source_world_id="W_shawq",
                target_world_id="W_ishtiyaq",
                merge_type="NEAR_SYNONYM",
                confidence=0.88,
                conflict_analysis={
                    "claim_overlap": 0.72,
                    "dimension_alignment": 0.85,
                    "conflicting_claims": 2,
                },
                evidence=[
                    {"type": "embedding_similarity", "score": 0.91},
                    {"type": "lexical", "relation": "near_synonym"},
                ],
                reasoning="High embedding similarity and overlapping claims suggest near-synonym",
            )
        ]

    async def _detect_splits(self, context: AgentContext) -> list[SplitCandidate]:
        """Detect Worlds that should be split."""
        # In production:
        # 1. Find Worlds with high internal claim variance
        # 2. Find Worlds spanning multiple distinct dimensions
        # 3. Cluster claims within World
        # 4. If clusters are distinct, propose split

        return [
            SplitCandidate(
                world_id="W_khayal",
                proposed_worlds=[
                    {
                        "canonical_term": "خیال_تصوری",
                        "transliteration": "Khayal_Tasawwuri",
                        "dimension": "imagination_faculty",
                    },
                    {
                        "canonical_term": "خیال_وهمی",
                        "transliteration": "Khayal_Wahmi",
                        "dimension": "estimation_faculty",
                    },
                ],
                confidence=0.72,
                evidence=[
                    {"type": "claim_clustering", "clusters": 2, "silhouette": 0.68},
                    {"type": "dimension_span", "dimensions": ["faculty", "object", "process"]},
                ],
                reasoning="Claims cluster into two distinct faculties: imagination vs estimation",
            )
        ]

    def validate_proposal(self, proposal: AgentProposal[list[MergeCandidate | SplitCandidate]]) -> bool:
        if proposal.confidence < 0.6:
            return False
        for candidate in proposal.payload:
            if candidate.confidence < 0.5:
                return False
            if isinstance(candidate, MergeCandidate):
                if candidate.source_world_id == candidate.target_world_id:
                    return False
                if candidate.merge_type not in ("SYNONYM", "NEAR_SYNONYM", "SUBSUME"):
                    return False
        return True


class MergeSplitService:
    """Service to execute approved merge/split proposals."""

    def __init__(self, session) -> None:
        self._session = session

    def execute_merge(self, candidate: MergeCandidate) -> dict[str, Any]:
        """Execute an approved merge. Nothing disappears - old IDs become aliases."""
        # In production:
        # 1. Collect all claims from both Worlds
        # 2. Detect conflicts
        # 3. Create canonical World
        # 4. Mark source as MERGED, add redirect
        # 5. Update graph relations
        # 6. Re-embed

        return {
            "action": "merge",
            "source_id": candidate.source_world_id,
            "target_id": candidate.target_world_id,
            "redirect": f"{candidate.source_world_id} -> MERGED_INTO -> {candidate.target_world_id}",
            "claims_transferred": "all",
            "conflicts_flagged": candidate.conflict_analysis.get("conflicting_claims", 0),
        }

    def execute_split(self, candidate: SplitCandidate) -> dict[str, Any]:
        """Execute an approved split."""
        # In production:
        # 1. Create new Worlds from proposed_worlds
        # 2. Distribute claims to appropriate new World
        # 3. Mark original as SUPERSEDED
        # 4. Update graph relations
        # 5. Re-embed

        return {
            "action": "split",
            "original_id": candidate.world_id,
            "new_worlds": [w["canonical_term"] for w in candidate.proposed_worlds],
            "original_status": "SUPERSEDED",
        }