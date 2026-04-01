"""
Step 5: Condition Prediction
- Suggests top 1–3 conditions with confidence scores
- Uses RAG context + LLM probabilistic reasoning
- Returns empty list when symptoms are too vague (honest uncertainty)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.pipeline.schemas import (
    PipelineContext,
    Condition,
    ConditionPredictionResult,
)
from app.services.llm_client import call_llm, parse_json_response, LLMError
from app.utils.logger import get_logger

logger = get_logger("step.condition_prediction")

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "diagnosis.txt"

STANDARD_CAVEAT = (
    "These suggestions are for general information only. "
    "Only a licensed healthcare professional can provide a real diagnosis."
)


def run(ctx: PipelineContext) -> PipelineContext:
    """Predict likely conditions from symptoms and RAG context."""
    t0 = time.monotonic()

    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []

    # Skip if no symptoms extracted
    if not symptoms:
        logger.info("step_condition_prediction_skipped", reason="no_symptoms")
        ctx.condition_result = ConditionPredictionResult(
            conditions=[],
            caveat=STANDARD_CAVEAT,
            source="fallback",
        )
        return ctx

    # Skip if emergency — conditions are irrelevant
    if ctx.red_flag_result and ctx.red_flag_result.triggered:
        logger.info("step_condition_prediction_skipped", reason="emergency_override")
        ctx.condition_result = ConditionPredictionResult(
            conditions=[],
            caveat="Emergency detected — seek immediate care.",
            source="fallback",
        )
        return ctx

    logger.info("step_condition_prediction_start", symptom_count=len(symptoms))

    symptoms_json = json.dumps([s.dict() for s in symptoms], indent=2)
    risk_level = ctx.risk_result.risk_level if ctx.risk_result else "low"
    rag_context = (
        "\n\n---\n\n".join(ctx.rag_context[:3]) if ctx.rag_context else "No medical context available."
    )

    try:
        template = _PROMPT_PATH.read_text()
        prompt = (
            template
            .replace("{symptoms_json}", symptoms_json)
            .replace("{risk_level}", risk_level)
            .replace("{rag_context}", rag_context)
        )

        raw = call_llm(prompt)
        data = parse_json_response(raw)

        raw_conditions = data.get("conditions", [])

        conditions = [
            Condition(
                name=c.get("name", "Unknown"),
                confidence=max(0.0, min(1.0, float(c.get("confidence", 0.3)))),
                reasoning=c.get("reasoning", ""),
            )
            for c in raw_conditions
            if c.get("name")
        ][:3]  # cap at 3

        ctx.condition_result = ConditionPredictionResult(
            conditions=conditions,
            caveat=data.get("caveat", STANDARD_CAVEAT),
            source="llm",
        )

    except LLMError as e:
        logger.warning("step_condition_prediction_llm_failed", error=str(e))
        ctx.condition_result = ConditionPredictionResult(
            conditions=[],
            caveat=STANDARD_CAVEAT,
            source="fallback",
        )

    except Exception as e:
        logger.error("step_condition_prediction_error", error=str(e))
        ctx.condition_result = ConditionPredictionResult(
            conditions=[],
            caveat=STANDARD_CAVEAT,
            source="fallback",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_condition_prediction_done",
        condition_count=len(ctx.condition_result.conditions),
        source=ctx.condition_result.source,
        elapsed_ms=elapsed_ms,
    )

    return ctx
