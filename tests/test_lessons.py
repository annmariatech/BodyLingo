"""API contract tests for lesson retrieval and explanations."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_does_not_depend_on_ai_service() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lesson_list_returns_summaries() -> None:
    response = client.get("/api/lessons")

    assert response.status_code == 200
    lessons = response.json()
    assert len(lessons) >= 5
    assert {
        "id",
        "title",
        "description",
        "topic",
        "difficulty",
        "estimated_duration_minutes",
        "learning_objectives",
        "communication_context",
    }.issubset(lessons[0])
    assert "introduction" not in lessons[0]


def test_retrieve_existing_lesson() -> None:
    response = client.get("/api/lessons/facial-expressions")

    assert response.status_code == 200
    lesson = response.json()
    assert lesson["id"] == "facial-expressions"
    assert lesson["introduction"]
    assert lesson["communication_cue"]
    assert lesson["examples"]
    assert lesson["knowledge_check"]
    assert lesson["key_takeaway"]


def test_unknown_lesson_returns_clear_404() -> None:
    response = client.get("/api/lessons/not-a-lesson")

    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found"}


def test_valid_explanation_request_uses_local_fallback() -> None:
    response = client.post(
        "/api/lessons/facial-expressions/explain",
        json={
            "question": "What might a frown mean?",
            "context": "During a meeting",
            "profile_preferences": {"format": "direct"},
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["explanation"]
    assert result["example"]
    assert result["alternative_interpretations"]
    assert result["communication_tip"]
    assert result["reminder"]
    assert result["provider"] == "deterministic_fallback"
    assert result["used_fallback"] is True


def test_empty_or_whitespace_explanation_request_is_rejected() -> None:
    for question in ("", "   "):
        response = client.post(
            "/api/lessons/facial-expressions/explain", json={"question": question}
        )
        assert response.status_code == 422


def test_excessively_long_explanation_request_is_rejected() -> None:
    response = client.post(
        "/api/lessons/facial-expressions/explain", json={"question": "x" * 1001}
    )

    assert response.status_code == 422


def test_malformed_explanation_request_is_rejected() -> None:
    response = client.post(
        "/api/lessons/facial-expressions/explain",
        json={"question": "Explain this", "unexpected": "field"},
    )

    assert response.status_code == 422


def test_unknown_lesson_explanation_returns_404() -> None:
    response = client.post("/api/lessons/not-a-lesson/explain", json={"question": "Help"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found"}
