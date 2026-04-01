"""
All ORM models in one place — no circular imports, easy to navigate.
"""
from __future__ import annotations
import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Text, Boolean, Float,
    DateTime, ForeignKey, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")


# ─── Conversation ─────────────────────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.created_at")


# ─── Message ──────────────────────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    decision_log: Mapped[Optional["DecisionLog"]] = relationship(back_populates="message", uselist=False)


# ─── DecisionLog ──────────────────────────────────────────────────────────────

class DecisionLog(Base):
    """
    One log per assistant reply — stores the full structured pipeline output.
    Used for explainability, auditing, and debugging.
    """
    __tablename__ = "decision_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), unique=True, nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Pipeline outputs (stored as JSON for flexibility)
    symptoms: Mapped[Optional[list]] = mapped_column(JSON)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))
    conditions: Mapped[Optional[list]] = mapped_column(JSON)
    advice: Mapped[Optional[str]] = mapped_column(Text)
    should_escalate: Mapped[bool] = mapped_column(Boolean, default=False)
    urgency: Mapped[Optional[str]] = mapped_column(String(30))
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    citations: Mapped[Optional[list]] = mapped_column(JSON)
    red_flags_triggered: Mapped[Optional[list]] = mapped_column(JSON)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    message: Mapped["Message"] = relationship(back_populates="decision_log")


# ─── MedicalDocument (RAG) ────────────────────────────────────────────────────

class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(200))
    source_file: Mapped[Optional[str]] = mapped_column(String(500))
    medical_domain: Mapped[Optional[str]] = mapped_column(String(100))
    chunk_index: Mapped[Optional[int]] = mapped_column(Integer)
    authority_level: Mapped[int] = mapped_column(Integer, default=1)
    embedding: Mapped[Optional[list]] = mapped_column(JSON)  # stored as JSON array
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
