"""
Step 8: Explanation Generation
- Human-readable reasoning for the assessment
- Builds user trust through transparency
- Fallback to template when LLM unavailable
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.pipeline.schemas import PipelineContext, ExplanationResult
from app.services.llm_client import call_llm, parse_json_response, LLMError
from app.utils.logger import get_logger

logger = get_logger("step.explanation")

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "explanation.txt"


def _fallback_explanation(ctx: PipelineContext) -> ExplanationResult:
    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []
    risk_level = ctx.risk_result.risk_level if ctx.risk_result else "low"
    conditions = ctx.condition_result.conditions if ctx.condition_result else []

    symptom_names = ", ".join(s.name for s in symptoms[:3]) if symptoms else "the reported symptoms"
    condition_names = ", ".join(c.name for c in conditions[:2]) if conditions else None

    explanation = (
        f"Based on {symptom_names}, the system classified the risk level as **{risk_level}**. "
    )

    if condition_names:
        explanation += (
            f"The symptoms are most consistent with {condition_names}, though other conditions are possible. "
        )

    explanation += (
        "This assessment was generated using medical knowledge and symptom analysis, "
        "but it is not a substitute for professional medical evaluation."
    )

    key_factors = [f"Symptom identified: {s.name}" for s in symptoms[:3]]
    if ctx.rag_used:
        key_factors.append("Relevant medical literature was found and used")
    else:
        key_factors.append("No specific medical literature matched — general guidelines used")

    return ExplanationResult(
        explanation=explanation,
        key_factors=key_factors,
        source="fallback",
    )


def run(ctx: PipelineContext) -> PipelineContext:
    """Generate a plain-language explanation of the pipeline reasoning."""
    t0 = time.monotonic()

    # Skip for emergency — explanation is the emergency response
    if ctx.red_flag_result and ctx.red_flag_result.triggered:
        flags = ctx.red_flag_result.flags[:2]
        ctx.explanation_result = ExplanationResult(
            explanation=(
                f"⚠️ Your message contained emergency warning signs: {', '.join(flags)}. "
                "The system immediately flagged this for emergency escalation. "
                "In a potential emergency, providing general medical information is unsafe — "
                "please contact emergency services directly."
            ),
            key_factors=[f"Emergency flag: {f}" for f in flags],
            source="deterministic",
        )
        return ctx

    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []
    risk_level = ctx.risk_result.risk_level if ctx.risk_result else "low"
    risk_reason = ctx.risk_result.risk_reason if ctx.risk_result else ""
    conditions = ctx.condition_result.conditions if ctx.condition_result else []

    logger.info("step_explanation_start")

    try:
        template = _PROMPT_PATH.read_text()
        prompt = (
            template
            .replace("{symptoms_json}", json.dumps([s.dict() for s in symptoms], indent=2))
            .replace("{risk_level}", risk_level)
            .replace("{conditions_json}", json.dumps([c.dict() for c in conditions], indent=2))
            .replace("{risk_reason}", risk_reason)
        )

        raw = call_llm(prompt)
        data = parse_json_response(raw)

        ctx.explanation_result = ExplanationResult(
            explanation=data.get("explanation", ""),
            key_factors=data.get("key_factors", []),
            source="llm",
        )

    except (LLMError, Exception) as e:
        logger.warning("step_explanation_fallback", error=str(e))
        ctx.explanation_result = _fallback_explanation(ctx)

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_explanation_done",
        source=ctx.explanation_result.source,
        elapsed_ms=elapsed_ms,
    )

    return ctx
