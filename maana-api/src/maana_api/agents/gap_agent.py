"""Gap Agent: detects missing Worlds in a Chapter/Cluster."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from maana_api.agents.base import Agent, AgentContext, AgentProposal, AgentType
from maana_api.domain.models import Scope


class GapCandidate(BaseModel):
    """A missing World candidate."""

    suggested_term: str
    suggested_transliteration: str | None = None
    reason: str
    dimension: str  # which semantic dimension is missing
    evidence: list[dict[str, Any]] = []
    confidence: float
    related_world_ids: list[str] = []


class GapAgent(Agent[list[GapCandidate]]):
    """Detects missing Worlds in a Chapter/Cluster based on central question and coverage."""

    def __init__(self) -> None:
        super().__init__(AgentType.GAP)

    async def run(self, context: AgentContext) -> list[AgentProposal[list[GapCandidate]]]:
        """Analyze coverage and detect gaps."""
        if not context.chapter_id and not context.cluster_id:
            return []

        candidates = await self._detect_gaps(context)

        if not candidates:
            return []

        proposal = self.create_proposal(
            payload=candidates,
            confidence=sum(c.confidence for c in candidates) / len(candidates),
            reasoning=f"Detected {len(candidates)} missing concepts for {context.chapter_id or context.cluster_id}",
            evidence=[e for c in candidates for e in c.evidence],
        )
        return [proposal]

    async def _detect_gaps(self, context: AgentContext) -> list[GapCandidate]:
        """Detect gaps by analyzing central question dimensions vs existing Worlds."""
        # In production:
        # 1. Load chapter/cluster central question
        # 2. Decompose into semantic dimensions
        # 3. Map existing Worlds to dimensions
        # 4. Find unmapped dimensions
        # 5. Use LKB + literature to suggest missing concepts

        # Placeholder candidates
        candidates = [
            GapCandidate(
                suggested_term="تخیل",
                suggested_transliteration="Takhayyul",
                reason="Philosophical dimension of imagination missing from literary cluster",
                dimension="philosophical",
                evidence=[{"source": "Ibn Sina", "concept": "quwwa al-takhayyul"}],
                confidence=0.85,
                related_world_ids=["W_khayal", "W_tasawwur"],
            ),
            GapCandidate(
                suggested_term="وهم",
                suggested_transliteration="Wahm",
                reason="Epistemic faculty between imagination and intellect not represented",
                dimension="epistemological",
                evidence=[{"source": "Suhrawardi", "concept": "al-wahm"}],
                confidence=0.78,
                related_world_ids=["W_khayal", "W_aql"],
            ),
        ]

        return candidates

    def validate_proposal(self, proposal: AgentProposal[list[GapCandidate]]) -> bool:
        if proposal.confidence < 0.6:
            return False
        for candidate in proposal.payload:
            if candidate.confidence < 0.5:
                return False
            if not candidate.suggested_term:
                return False
        return True


class GapProposalService:
    """Service to convert gap proposals to World creation requests."""

    def __init__(self, session) -> None:
        self._session = session

    def candidates_to_worlds(self, proposal: AgentProposal[list[GapCandidate]]) -> list[dict[str, Any]]:
        """Convert gap candidates to World creation payloads."""
        worlds = []
        for candidate in proposal.payload:
            world_data = {
                "canonical_term": candidate.suggested_term,
                "transliteration": candidate.suggested_transliteration,
                "status": "proposed",
                "scope": Scope.GLOBAL.value,
                "semantic_dimensions": {candidate.dimension: candidate.reason},
                "provenance": [
                    {
                        "contributor_kind": "ai_system",
                        "source": "gap_agent",
                        "method": "gap_detection",
                        "evidence": candidate.evidence,
                    }
                ],
            }
            worlds.append(world_data)
        return worlds