"""
Step 3: Red Flag Detection — DETERMINISTIC ONLY.

This layer has ZERO LLM dependency.
It runs before any LLM call and can IMMEDIATELY override everything.

Safety guarantee: if ANY red flag is present, escalation is forced.
No LLM response can override this layer.
"""
from __future__ import annotations

import time
from app.pipeline.schemas import PipelineContext, RedFlagResult
from app.utils.logger import get_logger

logger = get_logger("step.red_flag_detection")


# ─── Red flag definitions ─────────────────────────────────────────────────────
# Each entry: (keyword_pattern, description, urgency_level)

EMERGENCY_FLAGS: list[tuple[str, str]] = [
    # Cardiac
    ("chest pain", "Chest pain — possible cardiac emergency"),
    ("chest tightness", "Chest tightness — possible cardiac emergency"),
    ("chest pressure", "Chest pressure — possible cardiac emergency"),
    # Respiratory
    ("difficulty breathing", "Difficulty breathing — respiratory emergency"),
    ("trouble breathing", "Trouble breathing — respiratory emergency"),
    ("can't breathe", "Cannot breathe — respiratory emergency"),
    ("cannot breathe", "Cannot breathe — respiratory emergency"),
    ("shortness of breath", "Shortness of breath — possible emergency"),
    ("severe shortness of breath", "Severe breathing difficulty — emergency"),
    # Neurological
    ("unconscious", "Loss of consciousness — neurological emergency"),
    ("unresponsive", "Unresponsive patient — emergency"),
    ("loss of consciousness", "Loss of consciousness — emergency"),
    ("fainted", "Fainting episode — possible cardiac/neurological emergency"),
    ("seizure", "Seizure — neurological emergency"),
    ("slurred speech", "Slurred speech — possible stroke"),
    ("face drooping", "Face drooping — possible stroke (FAST)"),
    ("face droop", "Face drooping — possible stroke (FAST)"),
    ("arm weakness", "One-sided arm weakness — possible stroke (FAST)"),
    ("sudden weakness", "Sudden weakness — possible stroke or neurological emergency"),
    ("sudden numbness", "Sudden numbness — possible stroke"),
    ("worst headache", "Worst headache of life — possible subarachnoid hemorrhage"),
    # Bleeding
    ("vomiting blood", "Vomiting blood — gastrointestinal emergency"),
    ("coughing blood", "Coughing blood — pulmonary emergency"),
    ("severe bleeding", "Severe bleeding — emergency"),
    ("heavy bleeding", "Heavy bleeding — emergency"),
    ("bleeding heavily", "Bleeding heavily — emergency"),
    # Anaphylaxis
    ("throat swelling", "Throat swelling — possible anaphylaxis"),
    ("tongue swelling", "Tongue swelling — possible anaphylaxis"),
    ("lips swelling", "Lip swelling — possible anaphylaxis"),
    # Overdose / poisoning
    ("overdose", "Overdose — toxicological emergency"),
    ("poisoning", "Poisoning — emergency"),
    ("took too many pills", "Possible overdose — emergency"),
]

SELF_HARM_FLAGS: list[tuple[str, str]] = [
    ("suicidal", "Suicidal ideation — mental health emergency"),
    ("kill myself", "Suicidal ideation — mental health emergency"),
    ("want to die", "Suicidal ideation — mental health emergency"),
    ("self harm", "Self-harm — mental health emergency"),
    ("hurt myself", "Self-harm — mental health emergency"),
]

# Context-specific: serious only when combined with context
PREGNANCY_CONTEXT = {"pregnant", "pregnancy", "expecting"}
PREGNANCY_EMERGENCY_FLAGS = [
    "heavy bleeding",
    "severe abdominal pain",
    "no fetal movement",
    "water broke",
]

PEDIATRIC_CONTEXT = {"baby", "infant", "newborn", "3 month", "6 month", "toddler"}
PEDIATRIC_EMERGENCY_FLAGS = [
    "not breathing",
    "not feeding",
    "very lethargic",
    "limp",
    "high fever baby",
    "rash baby",
    "blue lips",
]

# ─── EMERGENCY RESPONSE MESSAGE ───────────────────────────────────────────────

EMERGENCY_RESPONSE = """⚠️ **This sounds like it could be a medical emergency.**

**Please call emergency services (112 / 911) immediately or go to your nearest emergency room.**

Do not wait. Do not drive yourself if you feel unwell — ask someone to help you.

**While waiting for help:**
- Stay as still and calm as possible
- Do not eat or drink anything
- Stay on the phone with emergency services

---
*AI Medibot cannot provide emergency care. In a life-threatening situation, only emergency medical services can help.*"""


def _check_flags(text: str, flags: list[tuple[str, str]]) -> list[str]:
    """Return descriptions of all triggered flags."""
    triggered = []
    for keyword, description in flags:
        if keyword in text:
            triggered.append(description)
    return triggered


def run(ctx: PipelineContext) -> PipelineContext:
    """
    Deterministic red flag scan. No LLM. No exceptions.
    If triggered: sets urgency=emergency, should_escalate=True.
    """
    t0 = time.monotonic()
    text = ctx.user_message.lower()

    logger.info("step_red_flag_detection_start")

    triggered_flags: list[str] = []

    # 1. Emergency symptom flags
    triggered_flags.extend(_check_flags(text, EMERGENCY_FLAGS))

    # 2. Self-harm flags
    triggered_flags.extend(_check_flags(text, SELF_HARM_FLAGS))

    # 3. Context-specific: pregnancy
    if any(kw in text for kw in PREGNANCY_CONTEXT):
        for kw in PREGNANCY_EMERGENCY_FLAGS:
            if kw in text:
                triggered_flags.append(f"Pregnancy red flag: {kw}")

    # 4. Context-specific: pediatric
    if any(kw in text for kw in PEDIATRIC_CONTEXT):
        for kw in PEDIATRIC_EMERGENCY_FLAGS:
            if kw in text:
                triggered_flags.append(f"Pediatric red flag: {kw}")

    # Deduplicate
    triggered_flags = list(dict.fromkeys(triggered_flags))

    if triggered_flags:
        ctx.red_flag_result = RedFlagResult(
            triggered=True,
            flags=triggered_flags,
            urgency="emergency",
            should_escalate=True,
        )
        # Force override of risk level
        if ctx.risk_result:
            ctx.risk_result.risk_level = "high"
            ctx.risk_result.risk_reason = f"Red flag override: {triggered_flags[0]}"
    else:
        ctx.red_flag_result = RedFlagResult(
            triggered=False,
            flags=[],
            urgency="none",
            should_escalate=False,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_red_flag_detection_done",
        triggered=ctx.red_flag_result.triggered,
        flag_count=len(triggered_flags),
        elapsed_ms=elapsed_ms,
    )

    return ctx


def get_emergency_response() -> str:
    return EMERGENCY_RESPONSE
