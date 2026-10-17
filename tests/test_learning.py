"""Learning preferences, scoring, progress and entitlement API tests."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models.learning  # noqa: F401
import models.user  # noqa: F401


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-two-test-secret-key-at-least-32-chars")
    monkeypatch.setenv("ENABLE_DEMO_PREMIUM", "0")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        session = sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def auth_headers(client: TestClient, username: str = "learner") -> dict[str, str]:
    response = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "safe-learning-password",
    })
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_preferences_persist_and_recommendations_use_chosen_topics(client: TestClient) -> None:
    headers = auth_headers(client)
    response = client.put("/api/learning/preferences", headers=headers, json={
        "topics": ["eye contact"],
        "situations": ["meetings"],
        "explanation_style": "examples",
        "communication_preferences": ["written steps"],
        "cultural_contexts": ["Japan"],
        "skipped": False,
    })
    assert response.status_code == 200
    assert client.get("/api/learning/preferences", headers=headers).json()["cultural_contexts"] == ["Japan"]
    picks = client.get("/api/learning/recommendations", headers=headers).json()
    assert picks[0]["id"] == "eye-contact"
    assert picks[0]["recommendation_reason"] == "Matches a topic you chose"


def test_quiz_hides_answers_scores_server_side_and_persists_completion(client: TestClient) -> None:
    headers = auth_headers(client)
    questions = client.get("/api/learning/lessons/facial-expressions/questions", headers=headers).json()
    assert len(questions) == 3
    assert "correct_option_id" not in questions[0]
    assert all("answer" not in option for question in questions for option in question["options"])

    first = questions[0]
    wrong = client.post(
        f"/api/learning/lessons/facial-expressions/attempts/{first['id']}",
        headers=headers,
        json={"question_id": first["id"], "selected_option_id": first["options"][0]["id"]},
    )
    assert wrong.status_code == 200
    wrong_result = wrong.json()
    assert wrong_result["correct"] is False
    assert datetime.fromisoformat(wrong_result["retry_due_at"]) > datetime.now(timezone.utc)
    scheduled = client.get("/api/learning/reviews", headers=headers).json()
    assert len(scheduled) == 1
    assert scheduled[0]["question"]["id"] == first["id"]
    assert scheduled[0]["is_due"] is False
    second_user = auth_headers(client, "second_learner")
    assert client.get("/api/learning/reviews", headers=second_user).json() == []

    for question in questions:
        correct_option = question["options"][1 if question["id"] == "expression-1" else (0 if question["id"] == "expression-2" else 1)]
        result = client.post(
            f"/api/learning/lessons/facial-expressions/attempts/{question['id']}",
            headers=headers,
            json={"question_id": question["id"], "selected_option_id": correct_option["id"]},
        )
        assert result.status_code == 200
    assert result.json()["completed"] is True
    progress = client.get("/api/learning/progress", headers=headers).json()
    assert progress["completed_lessons"] == ["facial-expressions"]
    assert progress["attempts"] == 4
    assert progress["correct_answers"] == 3
    assert progress["due_reviews"] == 0


def test_premium_content_requires_entitlement_and_demo_switch(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = auth_headers(client)
    locked = client.get("/api/lessons/space-and-breaks", headers=headers)
    assert locked.status_code == 403
    assert client.get("/api/learning/lessons/space-and-breaks/questions", headers=headers).status_code == 403
    assert client.post("/api/learning/premium/demo", headers=headers).status_code == 404

    monkeypatch.setenv("ENABLE_DEMO_PREMIUM", "1")
    assert client.post("/api/learning/premium/demo", headers=headers).json() == {"is_premium": True}
    unlocked = client.get("/api/lessons/space-and-breaks", headers=headers)
    assert unlocked.status_code == 200
    assert client.get("/api/learning/lessons/space-and-breaks/questions", headers=headers).status_code == 200


def test_learning_endpoints_require_authentication_and_reject_unknown_options(client: TestClient) -> None:
    assert client.get("/api/learning/progress").status_code == 401
    headers = auth_headers(client)
    response = client.post(
        "/api/learning/lessons/facial-expressions/attempts/expression-1",
        headers=headers,
        json={"question_id": "expression-1", "selected_option_id": "invented"},
    )
    assert response.status_code == 404
