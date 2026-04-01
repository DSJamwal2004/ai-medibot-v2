"""
Step 4: RAG Retrieval
- Semantic search against medical knowledge base
- Enriches context for downstream steps
- Graceful fallback — pipeline continues without context
"""
from __future__ import annotations

import time
from sqlalchemy.orm import Session
from typing import Optional

from app.pipeline.schemas import PipelineContext
from app.utils.logger import get_logger

logger = get_logger("step.rag_retrieval")


def run(ctx: PipelineContext, db: Optional[Session] = None) -> PipelineContext:
    """Retrieve relevant medical context for the user's query."""
    t0 = time.monotonic()

    if not ctx.enable_rag or db is None:
        logger.info("step_rag_retrieval_skipped", reason="disabled_or_no_db")
        return ctx

    # If emergency already detected, skip RAG (we respond immediately)
    if ctx.red_flag_result and ctx.red_flag_result.triggered:
        logger.info("step_rag_retrieval_skipped", reason="emergency_override")
        return ctx

    logger.info("step_rag_retrieval_start")

    try:
        from app.services.rag_service import retrieve

        # Build query from symptoms + message
        symptoms = ctx.symptom_result.symptoms if ctx.symptom_result else []
        symptom_text = ", ".join(s.name for s in symptoms[:5])
        query = f"{symptom_text} {ctx.user_message}".strip() if symptom_text else ctx.user_message

        result = retrieve(query=query, db=db)

        ctx.rag_context = result.context_texts
        ctx.rag_citations = result.citations
        ctx.rag_confidence = result.confidence
        ctx.rag_used = bool(result.chunks)

    except Exception as e:
        logger.error("step_rag_retrieval_error", error=str(e))
        ctx.rag_context = []
        ctx.rag_citations = []
        ctx.rag_confidence = 0.0
        ctx.rag_used = False

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    logger.info(
        "step_rag_retrieval_done",
        chunks=len(ctx.rag_context),
        confidence=ctx.rag_confidence,
        elapsed_ms=elapsed_ms,
    )

    return ctx
