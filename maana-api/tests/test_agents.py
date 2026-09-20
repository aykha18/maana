"""Tests for agents."""

from __future__ import annotations

import pytest

from maana_api.agents import (
    AgentContext,
    AgentOrchestrator,
    AgentType,
    ArchitectAgent,
    RingEvalAgent,
    GapAgent,
    MergeSplitAgent,
    RelationAgent,
    get_orchestrator,
)


@pytest.fixture
def orchestrator():
    return get_orchestrator()


@pytest.fixture
def context():
    return AgentContext(
        world_ids=["W001", "W002", "W003"],
        chapter_id="CH001",
        cluster_id="CL001",
        scope="global",
    )


def test_orchestrator_initialization(orchestrator: AgentOrchestrator):
    assert orchestrator is not None
    assert AgentType.RELATION in orchestrator._agents
    assert AgentType.ARCHITECT in orchestrator._agents
    assert AgentType.RING_EVAL in orchestrator._agents
    assert AgentType.GAP in orchestrator._agents
    assert AgentType.MERGE_SPLIT in orchestrator._agents


def test_get_agent(orchestrator: AgentOrchestrator):
    agent = orchestrator.get_agent(AgentType.RELATION)
    assert agent is not None
    assert isinstance(agent, RelationAgent)

    agent = orchestrator.get_agent(AgentType.ARCHITECT)
    assert agent is not None
    assert isinstance(agent, ArchitectAgent)


@pytest.mark.asyncio
async def test_relation_agent(orchestrator: AgentOrchestrator, context: AgentContext):
    proposals = await orchestrator.run_agent(AgentType.RELATION, context)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.agent_type == AgentType.RELATION
    assert proposal.confidence > 0
    assert len(proposal.payload) > 0


@pytest.mark.asyncio
async def test_architect_agent(orchestrator: AgentOrchestrator, context: AgentContext):
    proposals = await orchestrator.run_agent(AgentType.ARCHITECT, context)
    assert len(proposals) >= 1
    proposal = proposals[0]
    assert proposal.agent_type == AgentType.ARCHITECT
    assert proposal.payload.proposal_type in ("RESTRUCTURE", "SPLIT_CHAPTER", "MERGE_CLUSTERS", "REORDER", "ADD_CLUSTER")


@pytest.mark.asyncio
async def test_ring_eval_agent(orchestrator: AgentOrchestrator, context: AgentContext):
    proposals = await orchestrator.run_agent(AgentType.RING_EVAL, context)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.agent_type == AgentType.RING_EVAL
    assert proposal.payload.chapter_id == context.chapter_id
    assert 0 <= proposal.payload.scores.semantic_coherence <= 1


@pytest.mark.asyncio
async def test_gap_agent(orchestrator: AgentOrchestrator, context: AgentContext):
    proposals = await orchestrator.run_agent(AgentType.GAP, context)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.agent_type == AgentType.GAP
    assert len(proposal.payload) > 0


@pytest.mark.asyncio
async def test_merge_split_agent(orchestrator: AgentOrchestrator, context: AgentContext):
    proposals = await orchestrator.run_agent(AgentType.MERGE_SPLIT, context)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.agent_type == AgentType.MERGE_SPLIT
    assert len(proposal.payload) > 0


@pytest.mark.asyncio
async def test_run_all_agents(orchestrator: AgentOrchestrator, context: AgentContext):
    results = await orchestrator.run_all(context)
    # 5 implemented agents (INGESTION is a placeholder)
    implemented = {
        AgentType.RELATION,
        AgentType.ARCHITECT,
        AgentType.RING_EVAL,
        AgentType.GAP,
        AgentType.MERGE_SPLIT,
    }
    assert len(results) == len(implemented)
    for agent_type in implemented:
        assert agent_type in results


def test_validate_proposal(orchestrator: AgentOrchestrator):
    # Valid relation proposal
    from maana_api.agents import RelationAgent, RelationCandidate, AgentProposal
    agent = RelationAgent()
    proposal = agent.create_proposal(
        payload=[RelationCandidate(
            source_world_id="W001",
            target_world_id="W002",
            relation_type="related_to",
            confidence=0.8,
            reasoning="test",
        )],
        confidence=0.8,
        reasoning="test",
    )
    assert orchestrator.validate_proposal(AgentType.RELATION, proposal)

    # Invalid - low confidence
    proposal_low = agent.create_proposal(
        payload=[RelationCandidate(
            source_world_id="W001",
            target_world_id="W002",
            relation_type="related_to",
            confidence=0.2,
            reasoning="test",
        )],
        confidence=0.3,
        reasoning="test",
    )
    assert not orchestrator.validate_proposal(AgentType.RELATION, proposal_low)