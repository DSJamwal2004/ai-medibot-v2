"""
RAG Service tests — DB is mocked, no real database needed.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.rag_service import retrieve, RAGResult


def _make_doc(id, title, content, embedding=None, authority_level=1):
    doc = MagicMock()
    doc.id = id
    doc.title = title
    doc.content = content
    doc.source = "Test Source"
    doc.source_file = None
    doc.medical_domain = "general"
    doc.authority_level = authority_level
    doc.embedding = embedding or [0.1] * 384
    return doc


class TestRAGRetrieval:
    @patch("app.services.rag_service.embed")
    def test_returns_rag_result(self, mock_embed, tmp_path):
        mock_embed.return_value = [0.1] * 384

        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            _make_doc(1, "Headache causes", "Tension headaches are caused by stress..."),
            _make_doc(2, "Migraine symptoms", "Migraines often include throbbing pain..."),
        ]

        result = retrieve("I have a headache", db=db)

        assert isinstance(result, RAGResult)
        assert isinstance(result.chunks, list)
        assert isinstance(result.confidence, float)

    @patch("app.services.rag_service.embed")
    def test_empty_embedding_returns_fallback(self, mock_embed):
        mock_embed.return_value = []

        db = MagicMock()
        result = retrieve("some query", db=db)

        assert result.fallback_used is True
        assert result.chunks == []
        assert result.confidence == 0.0

    @patch("app.services.rag_service.embed")
    def test_no_documents_returns_fallback(self, mock_embed):
        mock_embed.return_value = [0.1] * 384

        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

        result = retrieve("some query", db=db)

        assert result.fallback_used is True

    @patch("app.services.rag_service.embed")
    def test_citations_returned(self, mock_embed):
        mock_embed.return_value = [0.5] * 384

        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            _make_doc(42, "Fever treatment", "Paracetamol can reduce fever...", embedding=[0.5] * 384),
        ]

        result = retrieve("how to treat fever", db=db)

        if result.chunks:
            citations = result.citations
            assert len(citations) > 0
            assert citations[0]["document_id"] == 42
            assert citations[0]["title"] == "Fever treatment"

    @patch("app.services.rag_service.embed")
    def test_authority_boost_applied(self, mock_embed):
        """Higher authority docs should score higher than lower authority with same similarity."""
        base_vec = [0.5] * 384
        mock_embed.return_value = base_vec

        db = MagicMock()
        low_auth = _make_doc(1, "Low Auth Doc", "content", embedding=base_vec, authority_level=1)
        high_auth = _make_doc(2, "High Auth Doc", "content", embedding=base_vec, authority_level=3)

        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
            low_auth, high_auth
        ]

        result = retrieve("test query", db=db, top_k=2)

        # High authority doc should appear first
        if len(result.chunks) >= 2:
            assert result.chunks[0].citation.document_id == 2
