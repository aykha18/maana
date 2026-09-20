"""Agent framework: base classes and protocols."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentType(StrEnum):
    """Types of agents in the Ma'na system."""

    RELATION = "relation"
    ARCHITECT = "architect"
    RING_EVAL = "ring_eval"
    GAP = "gap"
    MERGE_SPLIT = "merge_split"
    INGESTION = "ingestion"


class ProposalStatus(StrEnum):
    """Status of an agent proposal."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


T = TypeVar("T")


class AgentProposal(BaseModel, Generic[T]):
    """Base proposal from any agent."""

    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_type: AgentType
    status: ProposalStatus = ProposalStatus.DRAFT
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    payload: T
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: datetime | None = None
    reviewer_id: str | None = None


class AgentContext(BaseModel):
    """Context provided to agents for decision making."""

    world_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    chapter_id: str | None = None
    cluster_id: str | None = None
    scope: str = "global"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Agent(ABC, Generic[T]):
    """Base agent class. All agents produce proposals, never mutations."""

    def __init__(self, agent_type: AgentType) -> None:
        self.agent_type = agent_type

    @abstractmethod
    async def run(self, context: AgentContext) -> list[AgentProposal[T]]:
        """Execute the agent and return proposals."""
        ...

    @abstractmethod
    def validate_proposal(self, proposal: AgentProposal[T]) -> bool:
        """Validate a proposal before submission."""
        ...

    def create_proposal(
        self,
        payload: T,
        confidence: float,
        reasoning: str,
        evidence: list[dict[str, Any]] | None = None,
    ) -> AgentProposal[T]:
        """Create a proposal from the agent."""
        return AgentProposal(
            agent_type=self.agent_type,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence or [],
            payload=payload,
        )