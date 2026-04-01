"""
Step 6: Advice Generation
- Context-aware, safety-first, non-alarmist
- Adapts tone to risk level
- Uses RAG context to ground advice in medical literature
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.pipeline.schemas import PipelineContext, AdviceResult
from app.pipeline.step_red_flag_detection import get_emergency_response
from app.services.llm_client import call_llm, parse_json_response, LLMError
from app.utils.logger import get_logger

logger = get_logger("step.advice_generation")

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "advice.txt"

# Deterministic fallback advice by risk level
FALLBACK_ADVICE = {
    "low": {
        "advice": (
            "Based on what you've described, your symptoms appear to be mild. "
            "Rest, stay hydrated, and monitor how you feel over the next 24–48 hours."
        ),
        "immediate_steps": [
            "Rest and avoid strenuous activity",
            "Stay well hydrated",
            "Monitor your symptoms — if they worsen, seek medical advice",
        ],
        "when_to_seek_care": "Visit a doctor if symptoms persist for more than 3 days, worsen significantly, or new symptoms appear.",
        "tone": "reassuring",
    },
    "medium": {
        "advice": (
            "Your symptoms warrant attention. While not necessarily an emergency, "
            "you should consult a healthcare professional within the next 24–48 hours."
        ),
        "immediate_steps": [
            "Rest and avoid overexertion",
            "Stay hydrated — water and clear fluids",
            "Note when symptoms started and any changes",
            "Schedule an appointment with your doctor",
        ],
        "when_to_seek_care": "See a doctor within 24 hours. Go to emergency care immediately if symptoms worsen significantly.",
        "tone": "neutral",
    },
    "high": {
        "advice": (
            "Your symptoms are concerning and need prompt medical evaluation today. "
            "Please do not delay seeking care."
        ),
        "immediate_steps": [
            "Seek medical care today — do not wait",
            "If symptoms worsen suddenly, call emergency services",
            "Avoid driving yourself if you feel unwell",
            "Bring a list of your current medications",
        ],
        "when_to_seek_care": "Go to urgent care or an emergency room today. Call emergency services if symptoms worsen quickly.",
        "tone": "urgent",
    },
}


def run(ctx: PipelineContext) -> PipelineContext:
    """Generate practical, safety-aware advice."""
    t0 = time.monotonic()

    # Emergency override — return emergency response
    if ctx.red_flag_result and ctx.red_flag_result.triggered:
        ctx.advice_result = AdviceResult(
            advice=get_emergency_response(),
            immediate_steps=["Call emergency services (112/911) immediately"],
            when_to_seek_care="Emergency care NOW — do not wait.",
            tone="urgent",
            source="deterministic",
        )
        return ctx

    risk_level = ctx.risk_result.risk_level if ctx.risk_result else "low"
    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []

    logger.info("step_advice_generation_start", risk_level=risk_level)

    symptoms_json = json.dumps([s.dict() for s in symptoms], indent=2)
    conditions = ctx.condition_result.conditions if ctx.condition_result else []
    conditions_json = json.dumps([c.dict() for c in conditions], indent=2)
    rag_context = (
        "\n\n---\n\n".join(ctx.rag_context[:3]) if ctx.rag_context else "No medical context available."
    )

    try:
        template = _PROMPT_PATH.read_text()
        prompt = (
            template
            .replace("{symptoms_json}", symptoms_json)
            .replace("{risk_level}", risk_level)
            .replace("{conditions_json}", conditions_json)
            .replace("{rag_context}", rag_context)
        )

        raw = call_llm(prompt)
        data = parse_json_response(raw)

        ctx.advice_result = AdviceResult(
            advice=data.get("advice", ""),
            immediate_steps=data.get("immediate_steps", []),
            when_to_seek_care=data.get("when_to_seek_care", ""),
            tone=data.get("tone", "neutral"),
            source="llm",
        )

    except (LLMError, Exception) as e:
        logger.warning("step_advice_generation_fallback", error=str(e))
        fb = FALLBACK_ADVICE[risk_level]
        ctx.advice_result = AdviceResult(
            advice=fb["advice"],
            immediate_steps=fb["immediate_steps"],
            when_to_seek_care=fb["when_to_seek_care"],
            tone=fb["tone"],
            source="fallback",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_advice_generation_done",
        tone=ctx.advice_result.tone,
        source=ctx.advice_result.source,
        elapsed_ms=elapsed_ms,
    )

    return ctx
