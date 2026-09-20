"""Ring/Architecture Evaluation Agent: evaluates architectural quality across 7 dimensions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from maana_api.agents.base import Agent, AgentContext, AgentProposal, AgentType


class ArchitectureScores(BaseModel):
    """Multi-dimensional architecture evaluation scores."""

    semantic_coherence: float = Field(ge=0.0, le=1.0)
    transition_quality: float = Field(ge=0.0, le=1.0)
    central_question_alignment: float = Field(ge=0.0, le=1.0)
    redundancy: float = Field(ge=0.0, le=1.0)
    coverage: float = Field(ge=0.0, le=1.0)
    closure: float = Field(ge=0.0, le=1.0)
    asymmetry_justification: float = Field(ge=0.0, le=1.0)
    overall_architectural_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class RingEvaluation(BaseModel):
    """Complete ring evaluation result."""

    chapter_id: str
    scores: ArchitectureScores
    details: dict[str, Any] = {}
    recommendations: list[str] = []


class RingEvalAgent(Agent[RingEvaluation]):
    """Evaluates architectural quality across 7 dimensions. Symmetry is optional, coherence is primary."""

    def __init__(self) -> None:
        super().__init__(AgentType.RING_EVAL)

    async def run(self, context: AgentContext) -> list[AgentProposal[RingEvaluation]]:
        """Evaluate chapter/architecture quality."""
        if not context.chapter_id:
            return []

        evaluation = await self._evaluate_chapter(context)

        proposal = self.create_proposal(
            payload=evaluation,
            confidence=evaluation.scores.overall_architectural_confidence or 0.75,
            reasoning=self._generate_reasoning(evaluation),
            evidence=[{"type": "evaluation", "dimension": k, "score": v} for k, v in evaluation.scores.model_dump().items() if k != "overall_architectural_confidence"],
        )
        return [proposal]

    async def _evaluate_chapter(self, context: AgentContext) -> RingEvaluation:
        """Evaluate a chapter across all 7 dimensions."""
        # In production, this would:
        # 1. Load chapter structure (clusters, Worlds, relations)
        # 2. Compute each dimension:
        #    - semantic_coherence: average pairwise semantic similarity within clusters
        #    - transition_quality: relation strength between adjacent clusters
        #    - central_question_alignment: how well Worlds address chapter's central question
        #    - redundancy: duplicate/near-duplicate concepts
        #    - coverage: % of central question dimensions addressed
        #    - closure: whether the chapter forms a complete semantic journey
        #    - asymmetry_justification: are asymmetries semantically motivated?

        scores = ArchitectureScores(
            semantic_coherence=0.78,
            transition_quality=0.65,
            central_question_alignment=0.82,
            redundancy=0.15,
            coverage=0.71,
            closure=0.68,
            asymmetry_justification=0.90,
            overall_architectural_confidence=0.75,
        )

        return RingEvaluation(
            chapter_id=context.chapter_id or "unknown",
            scores=scores,
            details={
                "weak_transitions": ["cluster_2 -> cluster_3"],
                "missing_dimensions": ["philosophical_dimension"],
                "redundant_pairs": [("W1", "W2")],
            },
            recommendations=[
                "Add bridging concept between clusters 2 and 3",
                "Include philosophical dimension in cluster 1",
                "Review W1/W2 for potential merge",
            ],
        )

    def _generate_reasoning(self, evaluation: RingEvaluation) -> str:
        s = evaluation.scores
        parts = []
        if s.transition_quality < 0.7:
            parts.append(f"weak transitions ({s.transition_quality:.2f})")
        if s.coverage < 0.75:
            parts.append(f"incomplete coverage ({s.coverage:.2f})")
        if s.redundancy > 0.2:
            parts.append(f"high redundancy ({s.redundancy:.2f})")
        if not parts:
            parts.append("architecture is coherent")
        return f"Chapter {evaluation.chapter_id}: {', '.join(parts)}"

    def validate_proposal(self, proposal: AgentProposal[RingEvaluation]) -> bool:
        if proposal.confidence < 0.5:
            return False
        scores = proposal.payload.scores
        # At least one dimension should be meaningful
        return any(
            getattr(scores, dim) > 0
            for dim in [
                "semantic_coherence",
                "transition_quality",
                "central_question_alignment",
                "coverage",
                "closure",
            ]
        )