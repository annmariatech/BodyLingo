"""Connected API journey from account creation through progress and community."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.base import Base as ScenarioBase
from backend.models.scenario import Scenario
from database import Base, get_db
from main import app
import models.chat  # noqa: F401
import models.learning  # noqa: F401
import models.user  # noqa: F401
from services import chat_service


@pytest.fixture
def journey(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "full-journey-test-secret-key-at-least-32-chars")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    ScenarioBase.metadata.create_all(engine)
    with sessions() as db:
        db.add(Scenario(
            id="team-check-in",
            title="Checking in with a quiet teammate",
            description="A fictional workplace practice scenario.",
            learning_objectives=["Ask without assuming"],
            media_placeholder="Text-only practice; no media asset is included.",
            start_node_id="notice",
            nodes={"notice": {"prompt": "A teammate is quiet. What could you do?", "choices": [
                {"id": "ask-privately", "label": "Ask privately if they would like a check-in.", "next_node_id": None, "feedback": "A private question leaves room for many explanations."},
            ]}},
            published=True,
        ))
        db.commit()

    def override_get_db():
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    ScenarioBase.metadata.drop_all(engine)
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_registered_learner_completes_cross_feature_journey(journey: TestClient, monkeypatch: pytest.MonkeyPatch):
    client = journey
    preflight = client.options("/api/learning/preferences", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "PUT",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert preflight.status_code == 200
    assert "PUT" in preflight.headers["access-control-allow-methods"]

    registration = client.post("/api/auth/register", json={
        "username": "journey_learner",
        "email": "journey@example.com",
        "password": "a-long-safe-password",
    })
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}

    saved_preferences = client.put("/api/learning/preferences", headers=headers, json={
        "topics": ["Facial expressions"],
        "situations": ["Meetings and teamwork"],
        "explanation_style": "examples",
        "communication_preferences": ["Written steps"],
        "cultural_contexts": ["South Asia"],
        "skipped": False,
    })
    assert saved_preferences.status_code == 200
    recommendations = client.get("/api/learning/recommendations", headers=headers).json()
    facial_lesson = next(item for item in recommendations if item["id"] == "facial-expressions")
    assert facial_lesson["locked"] is False

    lesson = client.get("/api/lessons/facial-expressions", headers=headers)
    assert lesson.status_code == 200 and "answer" not in lesson.json()["knowledge_check"]
    questions = client.get("/api/learning/lessons/facial-expressions/questions", headers=headers).json()
    attempt = client.post("/api/learning/lessons/facial-expressions/attempts/expression-1", headers=headers, json={
        "question_id": "expression-1",
        "selected_option_id": "expression-1-option-1",
    })
    assert attempt.status_code == 200 and attempt.json()["correct"] is True
    assert len(questions) == 3

    scenario = client.get("/api/scenarios/team-check-in", headers=headers)
    assert scenario.status_code == 200
    response = client.post("/api/scenarios/team-check-in/respond", headers=headers, json={
        "current_step": "notice", "choice_id": "ask-privately",
    })
    assert response.status_code == 200 and response.json()["completed"] is True
    assert client.get("/api/scenarios/progress", headers=headers).json()["completed_scenarios"] == ["team-check-in"]

    monkeypatch.setattr(chat_service, "_groq_reply", lambda history, references: "A respectful check-in leaves room for context.")
    conversation = client.post("/api/chat/conversations", headers=headers).json()
    chat = client.post(f"/api/chat/conversations/{conversation['id']}/messages", headers=headers, json={
        "content": "How can I check in with a quiet teammate in a meeting?",
    })
    assert chat.status_code == 200
    assert {"type": "scenario", "id": "team-check-in", "title": "Checking in with a quiet teammate"} in chat.json()["references"]
    assert client.get(f"/api/chat/conversations/{conversation['id']}", headers=headers).json()["messages"][-1]["content"] == "A respectful check-in leaves room for context."

    feed = client.get("/api/forum/posts", headers=headers).json()
    filtered = client.get("/api/forum/posts", headers=headers, params={"query": "eye contact"}).json()
    assert len(feed["posts"]) == 8 and all(item["fictional"] for item in feed["posts"])
    assert [item["id"] for item in filtered["posts"]] == ["eye-contact-preferences"]

    profile = client.get("/api/auth/me", headers=headers).json()
    learning_progress = client.get("/api/learning/progress", headers=headers).json()
    scenario_progress = client.get("/api/scenarios/progress", headers=headers).json()
    assert profile["preferences"]["cultural_contexts"] == ["South Asia"]
    assert learning_progress["correct_answers"] == 1
    assert scenario_progress["sessions"][0]["response_count"] == 1

    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/learning/progress", headers=headers).status_code == 401
