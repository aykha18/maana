"""Relation Agent: discovers semantic relationships between Worlds."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from maana_api.agents.base import Agent, AgentContext, AgentProposal, AgentType
from maana_api.domain.models import Relation, RelationType, Scope, WorldStatus


class RelationCandidate(BaseModel):
    """A candidate relation proposed by the agent."""

    source_world_id: str
    target_world_id: str
    relation_type: RelationType
    confidence: float
    evidence: list[dict[str, Any]] = []
    reasoning: str


class RelationAgent(Agent[list[RelationCandidate]]):
    """Discovers semantic relationships between Worlds."""

    def __init__(self) -> None:
        super().__init__(AgentType.RELATION)

    async def run(self, context: AgentContext) -> list[AgentProposal[list[RelationCandidate]]]:
        """Analyze Worlds and propose relations."""
        candidates = await self._discover_relations(context)

        if not candidates:
            return []

        proposal = self.create_proposal(
            payload=candidates,
            confidence=self._aggregate_confidence(candidates),
            reasoning=f"Discovered {len(candidates)} candidate relations for {len(context.world_ids)} Worlds",
            evidence=[e for c in candidates for e in c.evidence],
        )
        return [proposal]

    async def _discover_relations(self, context: AgentContext) -> list[RelationCandidate]:
        """Discover candidate relations using vector similarity and graph traversal."""
        # In production, this would:
        # 1. Get World embeddings from vector store
        # 2. Find nearest neighbors
        # 3. Traverse graph for existing paths
        # 4. Use LLM to classify relation type
        # 5. Extract evidence from sources

        # Placeholder implementation
        candidates = []

        for i, source_id in enumerate(context.world_ids):
            for target_id in context.world_ids[i + 1 :]:
                # Vector similarity would determine if they're related
                # For now, create placeholder candidates
                candidate = RelationCandidate(
                    source_world_id=source_id,
                    target_world_id=target_id,
                    relation_type=RelationType.RELATED_TO,
                    confidence=0.75,
                    evidence=[],
                    reasoning=f"Vector similarity between {source_id} and {target_id} suggests relation",
                )
                candidates.append(candidate)

        return candidates

    def _aggregate_confidence(self, candidates: list[RelationCandidate]) -> float:
        if not candidates:
            return 0.0
        return sum(c.confidence for c in candidates) / len(candidates)

    def validate_proposal(self, proposal: AgentProposal[list[RelationCandidate]]) -> bool:
        if proposal.confidence < 0.5:
            return False
        for candidate in proposal.payload:
            if candidate.confidence < 0.3:
                return False
            if candidate.source_world_id == candidate.target_world_id:
                return False
        return True


class RelationProposalService:
    """Service to convert agent proposals to reviewable Relations."""

    def __init__(self, session) -> None:
        self._session = session

    def proposals_to_relations(self, proposal: AgentProposal[list[RelationCandidate]]) -> list[Relation]:
        """Convert approved proposals to Relation objects."""
        relations = []
        for candidate in proposal.payload:
            relation = Relation(
                relation_id=f"rel_{candidate.source_world_id}_{candidate.target_world_id}",
                relation_type=candidate.relation_type,
                source_world_id=candidate.source_world_id,
                target_world_id=candidate.target_world_id,
                status=WorldStatus.PROPOSED,
                scope=Scope.GLOBAL,
            )
            relations.append(relation)
        return relations