from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.models import Conversation, Message, DecisionLog
from app.pipeline.schemas import MedibotResponse
from app.utils.logger import get_logger

logger = get_logger("conversation_service")


def get_or_create_conversation(
    db: Session, user_id: int, conversation_id: Optional[int]
) -> Conversation:
    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if conv:
            return conv

    conv = Conversation(user_id=user_id)
    db.add(conv)
    db.flush()
    return conv


def auto_title(text: str, max_words: int = 6) -> str:
    words = text.strip().split()
    title = " ".join(words[:max_words])
    return title.capitalize() if title else "New conversation"


def save_user_message(db: Session, *, user_id: int, conversation_id: int, content: str) -> Message:
    msg = Message(user_id=user_id, conversation_id=conversation_id, role="user", content=content)
    db.add(msg)
    db.flush()

    # Auto-title conversation on first message
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv and not conv.title:
        conv.title = auto_title(content)

    return msg


def save_assistant_message(
    db: Session, *, user_id: int, conversation_id: int, content: str
) -> Message:
    msg = Message(
        user_id=user_id, conversation_id=conversation_id, role="assistant", content=content
    )
    db.add(msg)
    db.flush()
    return msg


def save_decision_log(
    db: Session,
    *,
    message_id: int,
    conversation_id: int,
    user_id: int,
    result: MedibotResponse,
    latency_ms: int,
) -> DecisionLog:
    log = DecisionLog(
        message_id=message_id,
        conversation_id=conversation_id,
        user_id=user_id,
        symptoms=[s.dict() for s in result.symptoms],
        risk_level=result.risk_level,
        conditions=[c.dict() for c in result.conditions],
        advice=result.advice,
        should_escalate=result.should_escalate,
        urgency=result.urgency,
        explanation=result.explanation,
        confidence_score=result.confidence_score,
        citations=[c.dict() for c in result.citations],
        red_flags_triggered=result.red_flags_triggered,
        llm_provider=result.llm_provider,
        latency_ms=latency_ms,
    )
    db.add(log)
    db.flush()
    return log


def get_conversation_history(
    db: Session, conversation_id: int, limit: int = 10
) -> list[dict]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def list_user_conversations(db: Session, user_id: int) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .all()
    )


def get_conversation_detail(
    db: Session, conversation_id: int, user_id: int
) -> Optional[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
