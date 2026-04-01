"""
Pipeline integration tests — LLM calls are mocked.
Tests the full pipeline flow and output contract.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.pipeline.schemas import PipelineContext, MedibotResponse
from app.pipeline import runner


# ── Shared mock LLM responses ─────────────────────────────────────────────────

SYMPTOM_LLM_RESPONSE = json.dumps({
    "symptoms": [
        {"name": "headache", "raw": "head hurts", "duration": "2 days", "severity": "moderate"},
        {"name": "fever", "raw": "fever", "duration": None, "severity": "mild"},
    ],
    "symptom_count": 2,
    "extraction_note": None,
})

RISK_LLM_RESPONSE = json.dumps({
    "risk_level": "medium",
    "risk_reason": "Fever combined with persistent headache warrants attention",
    "concerning_combinations": ["headache + fever"],
})

CONDITION_LLM_RESPONSE = json.dumps({
    "conditions": [
        {"name": "Viral infection", "confidence": 0.75, "reasoning": "Fever and headache are common viral symptoms"},
        {"name": "Tension headache", "confidence": 0.45, "reasoning": "Headache for 2 days without other features"},
    ],
    "caveat": "Only a doctor can diagnose. These are general possibilities.",
})

ADVICE_LLM_RESPONSE = json.dumps({
    "advice": "Rest and stay hydrated. Monitor your temperature.",
    "immediate_steps": ["Rest", "Drink fluids", "Take OTC fever reducer if over 38.5°C"],
    "when_to_seek_care": "See a doctor if fever exceeds 39.5°C or persists beyond 3 days.",
    "tone": "neutral",
})

EXPLANATION_LLM_RESPONSE = json.dumps({
    "explanation": "Your symptoms of headache and fever suggest a viral illness. The risk was classified as medium.",
    "key_factors": ["Fever present", "Headache lasting 2 days"],
})

LLM_SEQUENCE = [
    SYMPTOM_LLM_RESPONSE,
    RISK_LLM_RESPONSE,
    CONDITION_LLM_RESPONSE,
    ADVICE_LLM_RESPONSE,
    EXPLANATION_LLM_RESPONSE,
]


class TestPipelineOutputContract:
    """Verify the pipeline returns the full MedibotResponse contract."""

    @patch("app.services.llm_client.call_llm")
    def test_returns_medibot_response(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("I have a headache and fever for 2 days", db=None, enable_rag=False)

        assert isinstance(result, MedibotResponse)

    @patch("app.services.llm_client.call_llm")
    def test_symptoms_extracted(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("I have a headache and fever", db=None, enable_rag=False)

        assert len(result.symptoms) > 0
        symptom_names = [s.name for s in result.symptoms]
        assert "headache" in symptom_names

    @patch("app.services.llm_client.call_llm")
    def test_risk_level_is_valid(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("I have a headache and fever", db=None, enable_rag=False)

        assert result.risk_level in ("low", "medium", "high")

    @patch("app.services.llm_client.call_llm")
    def test_conditions_have_confidence(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("I have a headache and fever", db=None, enable_rag=False)

        for condition in result.conditions:
            assert 0.0 <= condition.confidence <= 1.0
            assert isinstance(condition.name, str)

    @patch("app.services.llm_client.call_llm")
    def test_confidence_score_range(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("I have a headache and fever", db=None, enable_rag=False)

        assert 0.0 <= result.confidence_score <= 1.0

    @patch("app.services.llm_client.call_llm")
    def test_urgency_valid_enum(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("I have a headache and fever", db=None, enable_rag=False)

        assert result.urgency in ("none", "consult_doctor", "emergency")

    @patch("app.services.llm_client.call_llm")
    def test_no_red_flags_for_mild_message(self, mock_llm):
        mock_llm.side_effect = LLM_SEQUENCE.copy()

        result = runner.run_pipeline("mild headache for one day", db=None, enable_rag=False)

        assert result.red_flags_triggered == []
        assert result.urgency != "emergency"


class TestEmergencyBypass:
    """Emergency should bypass all LLM steps."""

    @patch("app.services.llm_client.call_llm")
    def test_emergency_message_no_conditions(self, mock_llm):
        # LLM should be called for symptom extraction and possibly risk, but
        # condition prediction is skipped for emergencies
        mock_llm.side_effect = [SYMPTOM_LLM_RESPONSE, RISK_LLM_RESPONSE]

        result = runner.run_pipeline("I have chest pain and cannot breathe", db=None, enable_rag=False)

        assert result.urgency == "emergency"
        assert result.should_escalate is True
        assert "emergency" in result.advice.lower() or "⚠️" in result.advice
        assert len(result.red_flags_triggered) > 0

    def test_emergency_risk_overridden_to_high(self):
        """Red flag detection must force risk to high regardless of LLM."""
        with patch("app.services.llm_client.call_llm") as mock_llm:
            mock_llm.side_effect = [
                SYMPTOM_LLM_RESPONSE,
                json.dumps({"risk_level": "low", "risk_reason": "minimal", "concerning_combinations": []}),
            ]
            result = runner.run_pipeline("I have chest pain", db=None, enable_rag=False)

        assert result.risk_level == "high"


class TestOfflineMode:
    """Pipeline must work without any LLM available."""

    @patch("app.services.llm_client.call_llm")
    def test_offline_fallbacks_produce_valid_output(self, mock_llm):
        from app.services.llm_client import LLMError
        mock_llm.side_effect = LLMError("No LLM configured")

        result = runner.run_pipeline("I have a cough and runny nose", db=None, enable_rag=False)

        # Must return valid response even in offline mode
        assert isinstance(result, MedibotResponse)
        assert result.risk_level in ("low", "medium", "high")
        assert result.advice != ""
        assert result.urgency in ("none", "consult_doctor", "emergency")
