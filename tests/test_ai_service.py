"""Offline unit tests for the deterministic explanation service."""

from models.lesson import ExplanationRequest, Lesson
from services.ai_service import explain_lesson
from services.lesson_service import get_lessons


def test_explanation_fallback_works_without_provider_configuration() -> None:
    lesson = get_lessons()["eye-contact"]

    response = explain_lesson(
        lesson, ExplanationRequest(question="Does looking away mean disinterest?")
    )

    assert response.provider == "deterministic_fallback"
    assert response.used_fallback is True
    assert "eye contact" in response.explanation.lower()
    assert "neurotype" in response.reminder


def test_explanation_service_accepts_a_minimal_valid_lesson() -> None:
    lesson = Lesson(
        id="sample",
        title="Sample",
        description="Sample lesson",
        topic="sample",
        difficulty="beginner",
        estimated_duration_minutes=1,
        learning_objectives=["Understand the sample"],
        communication_context="A sample context",
        introduction="Introduction",
        communication_cue="A cue",
        explanation="Cues can have different meanings.",
        examples=[],
        knowledge_check={"question": "What can you do?"},
        key_takeaway="Ask respectfully.",
    )

    response = explain_lesson(lesson, ExplanationRequest(question="Explain the cue"))

    assert response.example == lesson.key_takeaway
    assert response.used_fallback is True
