"""
Tests for Step 3: Red Flag Detection

These tests require NO mocking — the layer is fully deterministic.
This is the most critical test suite in the entire project.
"""
import pytest
from app.pipeline.schemas import PipelineContext
from app.pipeline import step_red_flag_detection


def make_ctx(message: str) -> PipelineContext:
    return PipelineContext(user_message=message, enable_rag=False)


def run_flags(message: str):
    ctx = make_ctx(message)
    ctx = step_red_flag_detection.run(ctx)
    return ctx.red_flag_result


# ── Emergency triggers ────────────────────────────────────────────────────────

class TestEmergencyTriggers:
    def test_chest_pain(self):
        r = run_flags("I have chest pain")
        assert r.triggered is True
        assert r.urgency == "emergency"
        assert r.should_escalate is True

    def test_chest_tightness(self):
        r = run_flags("feeling chest tightness since morning")
        assert r.triggered is True

    def test_difficulty_breathing(self):
        r = run_flags("I'm having difficulty breathing")
        assert r.triggered is True

    def test_cannot_breathe(self):
        r = run_flags("I cannot breathe properly")
        assert r.triggered is True

    def test_loss_of_consciousness(self):
        r = run_flags("she had loss of consciousness for 2 minutes")
        assert r.triggered is True

    def test_seizure(self):
        r = run_flags("he had a seizure this morning")
        assert r.triggered is True

    def test_slurred_speech(self):
        r = run_flags("my speech is slurred and I feel weak")
        assert r.triggered is True

    def test_vomiting_blood(self):
        r = run_flags("I am vomiting blood")
        assert r.triggered is True

    def test_severe_bleeding(self):
        r = run_flags("severe bleeding from a wound")
        assert r.triggered is True

    def test_overdose(self):
        r = run_flags("I think I took an overdose")
        assert r.triggered is True

    def test_throat_swelling(self):
        r = run_flags("my throat swelling is getting worse")
        assert r.triggered is True

    def test_worst_headache(self):
        r = run_flags("worst headache of my life suddenly")
        assert r.triggered is True

    def test_face_drooping(self):
        r = run_flags("my face drooping on one side")
        assert r.triggered is True

    def test_sudden_weakness(self):
        r = run_flags("sudden weakness on my left side")
        assert r.triggered is True


# ── Self-harm triggers ────────────────────────────────────────────────────────

class TestSelfHarmTriggers:
    def test_suicidal(self):
        r = run_flags("I feel suicidal")
        assert r.triggered is True
        assert r.urgency == "emergency"

    def test_kill_myself(self):
        r = run_flags("I want to kill myself")
        assert r.triggered is True

    def test_self_harm(self):
        r = run_flags("I've been doing self harm")
        assert r.triggered is True


# ── Context-specific triggers ─────────────────────────────────────────────────

class TestContextSpecificTriggers:
    def test_pregnancy_heavy_bleeding(self):
        r = run_flags("I'm pregnant and have heavy bleeding")
        assert r.triggered is True

    def test_infant_not_breathing(self):
        r = run_flags("my baby is not breathing")
        assert r.triggered is True


# ── Should NOT trigger ────────────────────────────────────────────────────────

class TestNoFalsePositives:
    def test_informational_about_stroke(self):
        r = run_flags("what are the symptoms of a stroke?")
        assert r.triggered is False

    def test_mild_headache(self):
        r = run_flags("I have a mild headache")
        assert r.triggered is False

    def test_common_cold(self):
        r = run_flags("runny nose and slight cough for 2 days")
        assert r.triggered is False

    def test_asking_about_medication(self):
        r = run_flags("can I take ibuprofen with paracetamol?")
        assert r.triggered is False

    def test_general_fatigue(self):
        r = run_flags("I've been feeling tired lately")
        assert r.triggered is False

    def test_greeting(self):
        r = run_flags("hi, I need some help")
        assert r.triggered is False


# ── Urgency and escalation fields ─────────────────────────────────────────────

class TestOutputFields:
    def test_non_emergency_urgency(self):
        r = run_flags("I have a mild cold")
        assert r.urgency == "none"
        assert r.should_escalate is False
        assert r.flags == []

    def test_emergency_has_flag_descriptions(self):
        r = run_flags("I have chest pain and difficulty breathing")
        assert r.triggered is True
        assert len(r.flags) >= 2
        assert all(isinstance(f, str) for f in r.flags)
