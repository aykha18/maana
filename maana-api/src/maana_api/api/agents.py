"""Agent API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from maana_api.agents import (
    AgentContext,
    AgentOrchestrator,
    AgentProposal,
    AgentType,
    ProposalStatus,
    get_orchestrator,
)
from maana_api.infrastructure.database import get_db_session

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run/{agent_type}", response_model=list[AgentProposal[Any]])
async def run_agent(
    agent_type: AgentType,
    context: AgentContext,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> list[AgentProposal[Any]]:
    """Run a specific agent with the given context."""
    try:
        proposals = await orchestrator.run_agent(agent_type, context)
        return proposals
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/run-all", response_model=dict[AgentType, list[AgentProposal[Any]]])
async def run_all_agents(
    context: AgentContext,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> dict[AgentType, list[AgentProposal[Any]]]:
    """Run all agents with the given context."""
    return await orchestrator.run_all(context)


@router.post("/proposals/validate", response_model=bool)
def validate_proposal(
    agent_type: AgentType,
    proposal: AgentProposal[Any],
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> bool:
    """Validate a proposal using the agent's validator."""
    return orchestrator.validate_proposal(agent_type, proposal)


@router.post("/proposals/{proposal_id}/approve")
def approve_proposal(
    proposal_id: str,
    reviewer_id: str,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    """Approve a proposal (placeholder - would update proposal status in DB)."""
    # In production:
    # 1. Load proposal from DB
    # 2. Update status to APPROVED
    # 3. Execute proposal (create Relations, Worlds, etc.)
    # 4. Log audit trail
    return {
        "proposal_id": proposal_id,
        "status": ProposalStatus.APPROVED,
        "reviewer_id": reviewer_id,
        "message": "Proposal approved - implementation pending",
    }


@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(
    proposal_id: str,
    reviewer_id: str,
    reason: str,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    """Reject a proposal."""
    return {
        "proposal_id": proposal_id,
        "status": ProposalStatus.REJECTED,
        "reviewer_id": reviewer_id,
        "reason": reason,
    }


@router.get("/types", response_model=list[str])
def list_agent_types() -> list[str]:
    """List available agent types."""
    return [t.value for t in AgentType]