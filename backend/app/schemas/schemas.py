"""API-level schemas — request/response shapes for the HTTP layer."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class SymptomOut(BaseModel):
    name: str
    raw: str
    duration: Optional[str] = None
    severity: Optional[str] = None


class ConditionOut(BaseModel):
    name: str
    confidence: float
    reasoning: str = ""


class CitationOut(BaseModel):
    document_id: int
    title: str
    source: Optional[str] = None
    medical_domain: Optional[str] = None
    authority_level: int = 1
    score: float = 0.0


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int

    # Structured pipeline output
    symptoms: list[SymptomOut]
    risk_level: Literal["low", "medium", "high"]
    conditions: list[ConditionOut]
    advice: str
    immediate_steps: list[str]
    when_to_seek_care: str
    should_escalate: bool
    urgency: Literal["none", "consult_doctor", "emergency"]
    red_flags_triggered: list[str]
    explanation: str
    key_factors: list[str]
    confidence_score: float
    citations: list[CitationOut]
    rag_used: bool
    llm_provider: str


# ─── Conversations ────────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    messages: list[MessageOut]

    class Config:
        from_attributes = True
