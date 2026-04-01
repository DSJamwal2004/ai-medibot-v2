"""
Pipeline output contract — every step returns typed data.
This is the enforced schema for ALL pipeline outputs.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─── Step outputs ─────────────────────────────────────────────────────────────

class Symptom(BaseModel):
    name: str
    raw: str
    duration: Optional[str] = None
    severity: Optional[Literal["mild", "moderate", "severe"]] = None


class SymptomExtractionResult(BaseModel):
    symptoms: list[Symptom] = Field(default_factory=list)
    symptom_count: int = 0
    extraction_note: Optional[str] = None
    source: str = "llm"  # "llm" | "fallback"


class RiskClassificationResult(BaseModel):
    risk_level: Literal["low", "medium", "high"] = "low"
    risk_reason: str = ""
    concerning_combinations: list[str] = Field(default_factory=list)
    source: str = "llm"  # "llm" | "rule" | "fallback"


class RedFlagResult(BaseModel):
    triggered: bool = False
    flags: list[str] = Field(default_factory=list)
    urgency: Literal["none", "consult_doctor", "emergency"] = "none"
    should_escalate: bool = False


class Condition(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class ConditionPredictionResult(BaseModel):
    conditions: list[Condition] = Field(default_factory=list)
    caveat: str = ""
    source: str = "llm"  # "llm" | "fallback"


class AdviceResult(BaseModel):
    advice: str = ""
    immediate_steps: list[str] = Field(default_factory=list)
    when_to_seek_care: str = ""
    tone: Literal["reassuring", "neutral", "urgent"] = "neutral"
    source: str = "llm"


class ConfidenceResult(BaseModel):
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    factors: dict[str, float] = Field(default_factory=dict)


class ExplanationResult(BaseModel):
    explanation: str = ""
    key_factors: list[str] = Field(default_factory=list)
    source: str = "llm"


# ─── Citation ─────────────────────────────────────────────────────────────────

class Citation(BaseModel):
    document_id: int
    title: str
    source: Optional[str] = None
    medical_domain: Optional[str] = None
    authority_level: int = 1
    score: float = 0.0


# ─── Final pipeline output ────────────────────────────────────────────────────

class MedibotResponse(BaseModel):
    """
    The strict output contract for every AI pipeline run.
    This is what the API returns to the frontend.
    """
    # Core output
    symptoms: list[Symptom]
    risk_level: Literal["low", "medium", "high"]
    conditions: list[Condition]
    advice: str
    immediate_steps: list[str]
    when_to_seek_care: str

    # Safety
    should_escalate: bool
    urgency: Literal["none", "consult_doctor", "emergency"]
    red_flags_triggered: list[str]

    # Explainability
    explanation: str
    key_factors: list[str]
    risk_reason: str

    # Meta
    confidence_score: float
    citations: list[Citation]
    llm_provider: str
    rag_used: bool
    rag_confidence: float


# ─── Pipeline context (passed between steps) ──────────────────────────────────

class PipelineContext(BaseModel):
    """Mutable context passed through the pipeline."""
    user_message: str
    conversation_history: list[dict] = Field(default_factory=list)
    enable_rag: bool = True

    # Filled in by steps
    symptom_result: Optional[SymptomExtractionResult] = None
    risk_result: Optional[RiskClassificationResult] = None
    red_flag_result: Optional[RedFlagResult] = None
    rag_context: list[str] = Field(default_factory=list)
    rag_citations: list[dict] = Field(default_factory=list)
    rag_confidence: float = 0.0
    rag_used: bool = False
    condition_result: Optional[ConditionPredictionResult] = None
    advice_result: Optional[AdviceResult] = None
    confidence_result: Optional[ConfidenceResult] = None
    explanation_result: Optional[ExplanationResult] = None
    llm_provider: str = "offline"

    class Config:
        arbitrary_types_allowed = True
