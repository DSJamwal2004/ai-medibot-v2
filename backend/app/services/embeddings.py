"""
Embedding service — thread-safe singleton.
Loads the model once on first use (lazy), then reuses forever.
"""
from __future__ import annotations

import threading
from typing import Optional
import numpy as np

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("embeddings")

_model = None
_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                logger.info("embedding_model_loading", model=settings.EMBEDDING_MODEL)
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
                logger.info("embedding_model_ready")
    return _model


def embed(text: str) -> list[float]:
    """Embed a single string. Returns empty list on failure."""
    try:
        model = _get_model()
        vec = model.encode(text, normalize_embeddings=True)
        return vec.tolist()
    except Exception as e:
        logger.error("embed_failed", error=str(e))
        return []


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
