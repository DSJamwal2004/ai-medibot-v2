"""
Step 2: Risk Classification
- Combines LLM reasoning + deterministic rule boosting
- Falls back to rule-based if LLM unavailable
- Never upgrades risk ABOVE red-flag level (red flag detection handles that)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.pipeline.schemas import PipelineContext, RiskClassificationResult
from app.services.llm_client import call_llm, parse_json_response, LLMError
from app.utils.logger import get_logger

logger = get_logger("step.risk_classification")

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "risk_classification.txt"

# Rule-based risk boosters (deterministic override when symptoms match)
MEDIUM_RISK_PATTERNS = [
    "high fever", "persistent fever", "fever for", "severe headache",
    "high temperature", "chest discomfort", "palpitations",
    "significant pain", "worsening", "getting worse",
]

HIGH_RISK_PATTERNS = [
    "cannot walk", "sudden severe", "worst headache", "stiff neck",
    "very high fever", "blood in urine", "blood in stool", "coughing blood",
    "severe abdominal pain", "sudden vision", "sudden hearing",
]


def _rule_based_risk(symptoms_text: str, message: str) -> str:
    """Deterministic risk floor based on symptom patterns."""
    combined = (symptoms_text + " " + message).lower()

    for pattern in HIGH_RISK_PATTERNS:
        if pattern in combined:
            return "high"

    for pattern in MEDIUM_RISK_PATTERNS:
        if pattern in combined:
            return "medium"

    return "low"


def run(ctx: PipelineContext) -> PipelineContext:
    """Classify risk level from symptoms using LLM + rule boosting."""
    t0 = time.monotonic()

    symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []
    symptoms_json = json.dumps([s.dict() for s in symptoms], indent=2)

    logger.info("step_risk_classification_start", symptom_count=len(symptoms))

    # Rule-based floor
    symptom_text = " ".join(s.name for s in symptoms)
    rule_risk = _rule_based_risk(symptom_text, ctx.user_message)

    try:
        template = _PROMPT_PATH.read_text()
        prompt = template.replace("{symptoms_json}", symptoms_json).replace(
            "{user_message}", ctx.user_message
        )
        raw = call_llm(prompt)
        data = parse_json_response(raw)

        llm_risk = data.get("risk_level", "low")

        # Take the HIGHER of LLM + rule-based (safety-first)
        risk_order = {"low": 0, "medium": 1, "high": 2}
        final_risk = (
            llm_risk
            if risk_order.get(llm_risk, 0) >= risk_order.get(rule_risk, 0)
            else rule_risk
        )

        ctx.risk_result = RiskClassificationResult(
            risk_level=final_risk,
            risk_reason=data.get("risk_reason", ""),
            concerning_combinations=data.get("concerning_combinations", []),
            source="llm",
        )

    except LLMError as e:
        logger.warning("step_risk_classification_llm_failed", error=str(e))
        ctx.risk_result = RiskClassificationResult(
            risk_level=rule_risk,
            risk_reason="Rule-based classification (offline mode)",
            source="rule",
        )

    except Exception as e:
        logger.error("step_risk_classification_error", error=str(e))
        ctx.risk_result = RiskClassificationResult(
            risk_level=rule_risk,
            risk_reason="Fallback classification",
            source="rule",
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_risk_classification_done",
        risk_level=ctx.risk_result.risk_level,
        source=ctx.risk_result.source,
        elapsed_ms=elapsed_ms,
    )

    return ctx
