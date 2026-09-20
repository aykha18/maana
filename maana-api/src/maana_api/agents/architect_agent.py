"""Architect Agent: proposes structural reorganizations of the knowledge architecture."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from maana_api.agents.base import Agent, AgentContext, AgentProposal, AgentType
from maana_api.domain.models import WorldStatus, Scope


class ArchitectureProposal(BaseModel):
    """A structural architecture proposal."""

    proposal_type: str  # "RESTRUCTURE", "SPLIT_CHAPTER", "MERGE_CLUSTERS", "REORDER"
    reason: str
    affected_worlds: list[str]
    affected_chapters: list[str] = []
    affected_clusters: list[str] = []
    current_architecture: dict[str, Any] = {}
    proposed_architecture: dict[str, Any] = {}
    impact_assessment: dict[str, Any] = {}


class ArchitectAgent(Agent[ArchitectureProposal]):
    """Proposes structural reorganizations. Produces proposals, not mutations."""

    def __init__(self) -> None:
        super().__init__(AgentType.ARCHITECT)

    async def run(self, context: AgentContext) -> list[AgentProposal[ArchitectureProposal]]:
        """Analyze architecture and propose improvements."""
        proposals = []

        if context.chapter_id:
            # Analyze chapter structure
            chapter_proposal = await self._analyze_chapter(context)
            if chapter_proposal:
                proposals.append(chapter_proposal)

        if context.cluster_id:
            # Analyze cluster structure
            cluster_proposal = await self._analyze_cluster(context)
            if cluster_proposal:
                proposals.append(cluster_proposal)

        return proposals

    async def _analyze_chapter(self, context: AgentContext) -> AgentProposal[ArchitectureProposal] | None:
        """Analyze a chapter for structural issues."""
        # In production:
        # 1. Load chapter Worlds and their relations
        # 2. Check coherence, transitions, coverage, redundancy
        # 3. Identify issues: gaps, cycles, weak transitions, orphan Worlds
        # 4. Propose reordering, splitting, merging, adding

        proposal = ArchitectureProposal(
            proposal_type="RESTRUCTURE",
            reason="Chapter has weak semantic transitions between clusters",
            affected_worlds=context.world_ids,
            affected_chapters=[context.chapter_id] if context.chapter_id else [],
            current_architecture={"clusters": ["A", "B", "C"], "transitions": "weak"},
            proposed_architecture={"clusters": ["A", "X", "B", "C"], "transitions": "strong"},
            impact_assessment={
                "worlds_affected": len(context.world_ids),
                "relations_to_update": 5,
                "estimated_coherence_improvement": 0.23,
            },
        )

        return self.create_proposal(
            payload=proposal,
            confidence=0.82,
            reasoning="Detected 3 weak transitions and 1 missing bridging concept",
            evidence=[
                {"type": "transition_analysis", "from": "A", "to": "B", "score": 0.3},
                {"type": "missing_bridge", "concept": "X", "supporting_claims": 2},
            ],
        )

    async def _analyze_cluster(self, context: AgentContext) -> AgentProposal[ArchitectureProposal] | None:
        """Analyze a cluster for structural issues."""
        # Similar to chapter analysis but at cluster level
        return None

    def validate_proposal(self, proposal: AgentProposal[ArchitectureProposal]) -> bool:
        if proposal.confidence < 0.6:
            return False
        p = proposal.payload
        if not p.affected_worlds and not p.affected_chapters:
            return False
        if p.proposal_type not in ("RESTRUCTURE", "SPLIT_CHAPTER", "MERGE_CLUSTERS", "REORDER", "ADD_CLUSTER"):
            return False
        return True