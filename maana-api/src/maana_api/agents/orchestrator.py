"""Agent orchestrator: runs agents and manages proposal lifecycle."""

from __future__ import annotations

from typing import Any

from maana_api.agents.base import Agent, AgentContext, AgentProposal, AgentType
from maana_api.agents.relation_agent import RelationAgent
from maana_api.agents.architect_agent import ArchitectAgent
from maana_api.agents.ring_eval_agent import RingEvalAgent
from maana_api.agents.gap_agent import GapAgent
from maana_api.agents.merge_split_agent import MergeSplitAgent


class AgentOrchestrator:
    """Orchestrates agent execution and proposal management."""

    def __init__(self) -> None:
        self._agents: dict[AgentType, Agent] = {
            AgentType.RELATION: RelationAgent(),
            AgentType.ARCHITECT: ArchitectAgent(),
            AgentType.RING_EVAL: RingEvalAgent(),
            AgentType.GAP: GapAgent(),
            AgentType.MERGE_SPLIT: MergeSplitAgent(),
        }

    def get_agent(self, agent_type: AgentType) -> Agent | None:
        return self._agents.get(agent_type)

    async def run_agent(self, agent_type: AgentType, context: AgentContext) -> list[AgentProposal[Any]]:
        """Run a specific agent with context."""
        agent = self.get_agent(agent_type)
        if not agent:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return await agent.run(context)

    async def run_all(self, context: AgentContext) -> dict[AgentType, list[AgentProposal[Any]]]:
        """Run all agents with context."""
        results = {}
        for agent_type, agent in self._agents.items():
            try:
                results[agent_type] = await agent.run(context)
            except Exception as e:
                results[agent_type] = []
                # Log error in production
        return results

    def validate_proposal(self, agent_type: AgentType, proposal: AgentProposal[Any]) -> bool:
        """Validate a proposal using the agent's validator."""
        agent = self.get_agent(agent_type)
        if not agent:
            return False
        return agent.validate_proposal(proposal)


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator