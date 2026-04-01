"""
Step 1: Symptom Extraction
- Uses LLM to extract and normalize symptoms
- Falls back to basic keyword extraction if LLM unavailable
- Independent, testable, logs inputs + outputs
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from app.pipeline.schemas import PipelineContext, Symptom, SymptomExtractionResult
from app.services.llm_client import call_llm, parse_json_response, LLMError
from app.utils.logger import get_logger

logger = get_logger("step.symptom_extraction")

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "symptom_extraction.txt"


def _load_prompt(user_message: str) -> str:
    template = _PROMPT_PATH.read_text()
    return template.replace("{user_message}", user_message)


# Fallback: basic symptom keyword list for offline mode
SYMPTOM_KEYWORDS = [
    "headache", "fever", "cough", "pain", "nausea", "vomiting", "dizziness",
    "fatigue", "weakness", "rash", "swelling", "bleeding", "shortness of breath",
    "chest pain", "back pain", "abdominal pain", "diarrhea", "constipation",
    "sore throat", "runny nose", "itching", "numbness", "tingling",
]


def _fallback_extract(message: str) -> SymptomExtractionResult:
    """Basic keyword matching when LLM is unavailable."""
    text = message.lower()
    found = []
    for kw in SYMPTOM_KEYWORDS:
        if kw in text:
            found.append(Symptom(name=kw, raw=kw))

    return SymptomExtractionResult(
        symptoms=found,
        symptom_count=len(found),
        extraction_note="Offline keyword extraction (no LLM)",
        source="fallback",
    )


def run(ctx: PipelineContext) -> PipelineContext:
    """Extract and normalize symptoms from the user message."""
    t0 = time.monotonic()

    logger.info("step_symptom_extraction_start", message_len=len(ctx.user_message))

    try:
        prompt = _load_prompt(ctx.user_message)
        raw = call_llm(prompt)
        ctx.llm_provider = _get_provider_name()

        data = parse_json_response(raw)

        symptoms = [
            Symptom(
                name=s.get("name", ""),
                raw=s.get("raw", s.get("name", "")),
                duration=s.get("duration"),
                severity=s.get("severity"),
            )
            for s in data.get("symptoms", [])
            if s.get("name")
        ]

        ctx.symptom_result = SymptomExtractionResult(
            symptoms=symptoms,
            symptom_count=len(symptoms),
            extraction_note=data.get("extraction_note"),
            source="llm",
        )

    except LLMError as e:
        logger.warning("step_symptom_extraction_llm_failed", error=str(e))
        ctx.symptom_result = _fallback_extract(ctx.user_message)
        ctx.llm_provider = "offline"

    except Exception as e:
        logger.error("step_symptom_extraction_error", error=str(e))
        ctx.symptom_result = _fallback_extract(ctx.user_message)
        ctx.llm_provider = "offline"

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_symptom_extraction_done",
        symptom_count=ctx.symptom_result.symptom_count,
        source=ctx.symptom_result.source,
        elapsed_ms=elapsed_ms,
    )

    return ctx


def _get_provider_name() -> str:
    from app.core.config import settings
    return settings.LLM_PROVIDER
