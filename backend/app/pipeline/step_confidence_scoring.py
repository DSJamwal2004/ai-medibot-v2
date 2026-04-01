"""
Step 7: Confidence Scoring
- Aggregates signals from all previous steps
- Transparent: explains what drove the score
- Never reports false certainty
"""
from __future__ import annotations

import time
from app.pipeline.schemas import PipelineContext, ConfidenceResult
from app.utils.logger import get_logger

logger = get_logger("step.confidence_scoring")


def run(ctx: PipelineContext) -> PipelineContext:
    """Compute overall confidence score from pipeline signals."""
    t0 = time.monotonic()

    factors: dict[str, float] = {}

    # 1. Symptom clarity (how many symptoms were extracted clearly)
    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []
    symptom_score = min(1.0, len(symptoms) / 3.0) * 0.25
    factors["symptom_clarity"] = round(symptom_score, 3)

    # 2. RAG retrieval confidence
    rag_score = ctx.rag_confidence * 0.35 if ctx.rag_used else 0.0
    factors["rag_retrieval"] = round(rag_score, 3)

    # 3. LLM availability (did we actually run an LLM?)
    llm_score = 0.25 if ctx.llm_provider not in ("offline", "fallback", "") else 0.10
    factors["llm_quality"] = round(llm_score, 3)

    # 4. Condition prediction quality
    conditions = ctx.condition_result.conditions if ctx.condition_result else []
    if conditions:
        top_conf = conditions[0].confidence
        cond_score = top_conf * 0.15
    else:
        cond_score = 0.0
    factors["condition_confidence"] = round(cond_score, 3)

    raw_score = sum(factors.values())
    score = round(min(0.95, max(0.1, raw_score)), 3)

    ctx.confidence_result = ConfidenceResult(score=score, factors=factors)

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_confidence_scoring_done",
        score=score,
        factors=factors,
        elapsed_ms=elapsed_ms,
    )

    return ctx
