"""Scenario API integration tests for branching, persistence and ownership."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.base import Base as ScenarioBase
from backend.models.scenario import Scenario
from database import Base, get_db
from main import app
import models.learning  # noqa: F401
import models.user  # noqa: F401
import backend.models.scenario  # noqa: F401
import backend.models.scenario_response  # noqa: F401
import backend.models.scenario_session  # noqa: F401


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-three-test-secret-key-at-least-32-chars")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    ScenarioBase.metadata.create_all(engine)
    with sessions() as setup_db:
        setup_db.add(Scenario(
            id="quiet-teammate-meeting",
            title="A teammate becomes quiet",
            description="Offer a respectful check-in during a meeting.",
            learning_objectives=["Ask with care", "Respect communication choices"],
            media_placeholder="Text-only sample scenario; no media asset is included.",
            start_node_id="notice",
            nodes={
                "notice": {"prompt": "A teammate becomes quiet. What do you do?", "choices": [
                    {"id": "private-check-in", "label": "Check in privately.", "next_node_id": "check-in", "feedback": "A private question avoids putting them on the spot."},
                    {"id": "offer-option", "label": "Offer written input.", "next_node_id": "check-in", "feedback": "Choices can make participation easier."},
                    {"id": "assume-disinterest", "label": "Assume disinterest.", "next_node_id": "check-in", "feedback": "Quietness can have many explanations."},
                ]},
                "check-in": {"prompt": "They need more time. What next?", "choices": [
                    {"id": "ask-preference", "label": "Ask how they prefer to contribute.", "next_node_id": "support-reflection", "feedback": "Asking supports their choice."},
                ]},
                "support-reflection": {"prompt": "What gave them more control?", "choices": [
                    {"id": "finish-supportive", "label": "Offering a choice.", "next_node_id": None, "feedback": "Offering choices supports participation."},
                ]},
            },
        ))
        setup_db.commit()

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
    ScenarioBase.metadata.drop_all(engine)
    Base.metadata.drop_all(engine)
    engine.dispose()


def token_for(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "scenario-test-password",
    })
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_scenarios_branch_persist_resume_and_scope_progress_to_owner(client: TestClient) -> None:
    first_headers = token_for(client, "scenario_learner")
    second_headers = token_for(client, "other_learner")

    catalog = client.get("/api/scenarios", headers=first_headers)
    assert catalog.status_code == 200
    scenarios = catalog.json()["scenarios"]
    assert len(scenarios) == 1
    assert all(scenario["learning_objectives"] for scenario in scenarios)
    assert all("Text-only" in scenario["media_placeholder"] for scenario in scenarios)

    start = client.get("/api/scenarios/quiet-teammate-meeting", headers=first_headers)
    assert start.status_code == 200
    start_body = start.json()
    assert start_body["current_step"] == "notice"
    assert "next_node_id" not in start.text
    assert len(start_body["choices"]) == 3

    bad_choice = client.post("/api/scenarios/quiet-teammate-meeting/respond", headers=first_headers, json={
        "current_step": "notice", "choice_id": "made-up-choice",
    })
    assert bad_choice.status_code == 422

    first = client.post("/api/scenarios/quiet-teammate-meeting/respond", headers=first_headers, json={
        "current_step": "notice", "choice_id": "private-check-in",
    })
    assert first.status_code == 200
    assert first.json()["current_step"] == "check-in"
    assert first.json()["feedback"]

    stale = client.post("/api/scenarios/quiet-teammate-meeting/respond", headers=first_headers, json={
        "current_step": "notice", "choice_id": "offer-option",
    })
    assert stale.status_code == 409

    resumed = client.get("/api/scenarios/quiet-teammate-meeting", headers=first_headers)
    assert resumed.json()["current_step"] == "check-in"
    other_start = client.get("/api/scenarios/quiet-teammate-meeting", headers=second_headers)
    assert other_start.json()["current_step"] == "notice"
    assert client.get("/api/scenarios/progress", headers=second_headers).json()["sessions"] == []

    second = client.post("/api/scenarios/quiet-teammate-meeting/respond", headers=first_headers, json={
        "current_step": "check-in", "choice_id": "ask-preference",
    })
    assert second.json()["current_step"] == "support-reflection"
    final = client.post("/api/scenarios/quiet-teammate-meeting/respond", headers=first_headers, json={
        "current_step": "support-reflection", "choice_id": "finish-supportive",
    })
    assert final.json()["completed"] is True
    history = client.get("/api/scenarios/progress", headers=first_headers).json()
    assert history["completed_scenarios"] == ["quiet-teammate-meeting"]
    assert history["sessions"][0]["response_count"] == 3


def test_scenario_api_requires_authentication_and_hides_unpublished_scenarios(client: TestClient) -> None:
    assert client.get("/api/scenarios").status_code == 401
    headers = token_for(client, "another_learner")
    assert client.get("/api/scenarios/not-a-scenario", headers=headers).status_code == 404
