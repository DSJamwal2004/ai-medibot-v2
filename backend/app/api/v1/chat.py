"""
Chat API Route — intentionally thin.

This file contains ONLY:
- Request parsing
- Calling the pipeline runner
- Saving results to DB
- Returning the typed response

Business logic lives in app/pipeline/. Not here.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.pipeline.runner import run_pipeline
from app.services.conversation_service import (
    get_or_create_conversation,
    save_user_message,
    save_assistant_message,
    save_decision_log,
    get_conversation_history,
)
from app.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    SymptomOut,
    ConditionOut,
    CitationOut,
)
from app.utils.logger import get_logger
from app.core.config import settings

router = APIRouter(tags=["chat"])
logger = get_logger("api.chat")


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    t0 = time.monotonic()

    try:
        # ── 1. Get or create conversation ────────────────────────────────────
        conv = get_or_create_conversation(db, current_user.id, payload.conversation_id)

        # ── 2. Persist user message ───────────────────────────────────────────
        user_msg = save_user_message(
            db, user_id=current_user.id,
            conversation_id=conv.id,
            content=payload.message,
        )

        # ── 3. Build conversation history for pipeline context ────────────────
        history = get_conversation_history(db, conv.id, limit=8)

        # ── 4. Run the AI pipeline ────────────────────────────────────────────
        result = run_pipeline(
            user_message=payload.message,
            db=db,
            conversation_history=history,
            enable_rag=settings.ENABLE_RAG,
        )

        latency_ms = int((time.monotonic() - t0) * 1000)

        # ── 5. Persist assistant message ──────────────────────────────────────
        assistant_msg = save_assistant_message(
            db, user_id=current_user.id,
            conversation_id=conv.id,
            content=result.advice,
        )

        # ── 6. Persist decision log for auditing / explainability ─────────────
        save_decision_log(
            db,
            message_id=assistant_msg.id,
            conversation_id=conv.id,
            user_id=current_user.id,
            result=result,
            latency_ms=latency_ms,
        )

        db.commit()

        logger.info(
            "chat_complete",
            conversation_id=conv.id,
            risk_level=result.risk_level,
            urgency=result.urgency,
            latency_ms=latency_ms,
        )

        # ── 7. Return structured response ─────────────────────────────────────
        return ChatResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            symptoms=[SymptomOut(**s.dict()) for s in result.symptoms],
            risk_level=result.risk_level,
            conditions=[ConditionOut(**c.dict()) for c in result.conditions],
            advice=result.advice,
            immediate_steps=result.immediate_steps,
            when_to_seek_care=result.when_to_seek_care,
            should_escalate=result.should_escalate,
            urgency=result.urgency,
            red_flags_triggered=result.red_flags_triggered,
            explanation=result.explanation,
            key_factors=result.key_factors,
            confidence_score=result.confidence_score,
            citations=[CitationOut(**c.dict()) for c in result.citations],
            rag_used=result.rag_used,
            llm_provider=result.llm_provider,
        )

    except Exception as e:
        db.rollback()
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error processing your message")
