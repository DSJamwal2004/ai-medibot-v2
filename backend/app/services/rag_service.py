"""
RAG Service — clean semantic retrieval with honest fallbacks.

Design decisions:
- Embeddings stored as JSON arrays (no pgvector dependency — simpler deployment)
- In-memory similarity scoring after candidate fetch (scales fine for <100k docs)
- Explicit fallback when no good matches found
- Returns citations always
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.models import MedicalDocument
from app.services.embeddings import embed, cosine_similarity
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag")


@dataclass
class Citation:
    document_id: int
    title: str
    source: Optional[str]
    source_file: Optional[str]
    medical_domain: Optional[str]
    authority_level: int
    score: float


@dataclass
class RAGChunk:
    content: str
    citation: Citation
    score: float


@dataclass
class RAGResult:
    chunks: list[RAGChunk] = field(default_factory=list)
    confidence: float = 0.0
    fallback_used: bool = False

    @property
    def context_texts(self) -> list[str]:
        return [c.content for c in self.chunks]

    @property
    def citations(self) -> list[dict]:
        return [
            {
                "document_id": c.citation.document_id,
                "title": c.citation.title,
                "source": c.citation.source,
                "medical_domain": c.citation.medical_domain,
                "authority_level": c.citation.authority_level,
                "score": round(c.score, 3),
            }
            for c in self.chunks
        ]


AUTHORITY_BOOST = {1: 0.0, 2: 0.03, 3: 0.06}


def retrieve(
    query: str,
    db: Session,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
    medical_domain: Optional[str] = None,
) -> RAGResult:
    """
    Retrieve top-k relevant medical document chunks for a query.
    Returns RAGResult with chunks, confidence, and citations.
    """
    k = top_k or settings.RAG_TOP_K
    threshold = min_score if min_score is not None else settings.RAG_MIN_SCORE

    query_vec = embed(query)
    if not query_vec:
        logger.warning("rag_skipped_no_embedding")
        return RAGResult(fallback_used=True)

    # Fetch candidate documents (up to 200 for in-memory scoring)
    q = db.query(MedicalDocument)
    if medical_domain:
        q = q.filter(MedicalDocument.medical_domain == medical_domain)

    candidates = q.limit(200).all()

    if not candidates:
        logger.warning("rag_no_documents_in_db")
        return RAGResult(fallback_used=True)

    # Score all candidates
    scored: list[tuple[float, MedicalDocument]] = []
    for doc in candidates:
        if not doc.embedding:
            continue
        sim = cosine_similarity(query_vec, doc.embedding)
        auth_boost = AUTHORITY_BOOST.get(doc.authority_level or 1, 0.0)
        final_score = sim + auth_boost
        scored.append((final_score, doc))

    if not scored:
        return RAGResult(fallback_used=True)

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [(score, doc) for score, doc in scored[:k] if score >= threshold]

    # If nothing meets threshold, fall back to top results regardless
    fallback_used = False
    if not top:
        top = scored[:min(k, 2)]
        fallback_used = True
        logger.info("rag_fallback_used", reason="below_threshold", best_score=scored[0][0])

    chunks = [
        RAGChunk(
            content=doc.content,
            score=score,
            citation=Citation(
                document_id=doc.id,
                title=doc.title,
                source=doc.source,
                source_file=doc.source_file,
                medical_domain=doc.medical_domain,
                authority_level=doc.authority_level or 1,
                score=score,
            ),
        )
        for score, doc in top
    ]

    best_score = top[0][0] if top else 0.0
    coverage = len(chunks) / k
    confidence = round(min(1.0, best_score * 0.7 + coverage * 0.3), 3)

    logger.info(
        "rag_retrieved",
        chunks=len(chunks),
        best_score=round(best_score, 3),
        confidence=confidence,
        fallback=fallback_used,
    )

    return RAGResult(chunks=chunks, confidence=confidence, fallback_used=fallback_used)
