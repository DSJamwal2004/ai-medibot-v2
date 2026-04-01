"""
Pipeline Runner — orchestrates all 8 steps in sequence.

Each step:
  - receives the PipelineContext
  - enriches it with its output
  - returns the modified context

The runner assembles the final MedibotResponse from the context.
"""
from __future__ import annotations

import time
from typing import Optional

from sqlalchemy.orm import Session

from app.pipeline.schemas import (
    PipelineContext,
    MedibotResponse,
    Citation,
)
from app.pipeline import (
    step_symptom_extraction,
    step_risk_classification,
    step_red_flag_detection,
    step_rag_retrieval,
    step_condition_prediction,
    step_advice_generation,
    step_confidence_scoring,
    step_explanation,
)
from app.utils.logger import get_logger

logger = get_logger("pipeline.runner")

MEDICAL_DISCLAIMER = (
    "\n\n---\n*This information is for general guidance only and does not constitute "
    "medical advice. Always consult a qualified healthcare professional.*"
)


def run_pipeline(
    user_message: str,
    db: Optional[Session] = None,
    conversation_history: Optional[list[dict]] = None,
    enable_rag: bool = True,
) -> MedibotResponse:
    """
    Run the full AI medical reasoning pipeline.
    Returns a fully typed MedibotResponse.

    Steps:
    1. Symptom Extraction
    2. Risk Classification
    3. Red Flag Detection (deterministic, LLM-free)
    4. RAG Retrieval
    5. Condition Prediction
    6. Advice Generation
    7. Confidence Scoring
    8. Explanation Generation
    """
    t_total = time.monotonic()

    ctx = PipelineContext(
        user_message=user_message,
        conversation_history=conversation_history or [],
        enable_rag=enable_rag,
    )

    logger.info("pipeline_start", message_len=len(user_message))

    # ── Step 1: Symptom Extraction ────────────────────────────────────────────
    ctx = step_symptom_extraction.run(ctx)

    # ── Step 2: Risk Classification ───────────────────────────────────────────
    ctx = step_risk_classification.run(ctx)

    # ── Step 3: Red Flag Detection (DETERMINISTIC — always runs) ─────────────
    ctx = step_red_flag_detection.run(ctx)

    # ── Early exit: if emergency, skip RAG + conditions + advice elaboration ─
    if ctx.red_flag_result and ctx.red_flag_result.triggered:
        ctx = step_advice_generation.run(ctx)   # generates emergency message
        ctx = step_explanation.run(ctx)
        ctx = step_confidence_scoring.run(ctx)
        return _assemble(ctx, total_ms=int((time.monotonic() - t_total) * 1000))

    # ── Step 4: RAG Retrieval ─────────────────────────────────────────────────
    ctx = step_rag_retrieval.run(ctx, db=db)

    # ── Step 5: Condition Prediction ──────────────────────────────────────────
    ctx = step_condition_prediction.run(ctx)

    # ── Step 6: Advice Generation ─────────────────────────────────────────────
    ctx = step_advice_generation.run(ctx)

    # ── Step 7: Confidence Scoring ────────────────────────────────────────────
    ctx = step_confidence_scoring.run(ctx)

    # ── Step 8: Explanation Generation ───────────────────────────────────────
    ctx = step_explanation.run(ctx)

    total_ms = int((time.monotonic() - t_total) * 1000)
    logger.info("pipeline_complete", total_ms=total_ms)

    return _assemble(ctx, total_ms=total_ms)


def _assemble(ctx: PipelineContext, total_ms: int) -> MedibotResponse:
    """Assemble the final typed response from pipeline context."""

    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []
    risk_level = ctx.risk_result.risk_level if ctx.risk_result else "low"
    risk_reason = ctx.risk_result.risk_reason if ctx.risk_result else ""
    red_flag_result = ctx.red_flag_result
    conditions = ctx.condition_result.conditions if ctx.condition_result else []
    advice_result = ctx.advice_result
    confidence_result = ctx.confidence_result
    explanation_result = ctx.explanation_result

    # Safety: ensure advice has disclaimer
    advice_text = advice_result.advice if advice_result else ""
    if advice_text and not advice_text.startswith("⚠️"):
        advice_text += MEDICAL_DISCLAIMER

    citations = [
        Citation(
            document_id=c["document_id"],
            title=c["title"],
            source=c.get("source"),
            medical_domain=c.get("medical_domain"),
            authority_level=c.get("authority_level", 1),
            score=c.get("score", 0.0),
        )
        for c in ctx.rag_citations
    ]

    # Determine urgency
    if red_flag_result and red_flag_result.triggered:
        urgency = "emergency"
        should_escalate = True
    elif risk_level == "high":
        urgency = "consult_doctor"
        should_escalate = True
    elif risk_level == "medium":
        urgency = "consult_doctor"
        should_escalate = False
    else:
        urgency = "none"
        should_escalate = False

    return MedibotResponse(
        symptoms=symptoms,
        risk_level=risk_level,
        conditions=conditions,
        advice=advice_text,
        immediate_steps=advice_result.immediate_steps if advice_result else [],
        when_to_seek_care=advice_result.when_to_seek_care if advice_result else "",
        should_escalate=should_escalate,
        urgency=urgency,
        red_flags_triggered=red_flag_result.flags if red_flag_result else [],
        explanation=explanation_result.explanation if explanation_result else "",
        key_factors=explanation_result.key_factors if explanation_result else [],
        risk_reason=risk_reason,
        confidence_score=confidence_result.score if confidence_result else 0.5,
        citations=citations,
        llm_provider=ctx.llm_provider,
        rag_used=ctx.rag_used,
        rag_confidence=ctx.rag_confidence,
    )
