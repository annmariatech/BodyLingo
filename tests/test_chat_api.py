"""Chat persistence, isolation and provider behavior tests."""

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


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "chat-test-secret-key-at-least-32-characters")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    ScenarioBase.metadata.create_all(engine)
    with sessions() as db:
        db.add(Scenario(id="quiet-teammate", title="A quiet teammate", description="Check in with a teammate who is quiet in a meeting.", learning_objectives=["Ask respectfully"], media_placeholder="Text only", start_node_id="start", nodes={"start": {"prompt": "Check in", "choices": []}}, published=True))
        db.commit()

    def override_get_db():
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    ScenarioBase.metadata.drop_all(engine)
    Base.metadata.drop_all(engine)
    engine.dispose()


def auth(client: TestClient, username: str) -> dict[str, str]:
    result = client.post("/api/auth/register", json={"username": username, "email": f"{username}@example.com", "password": "a-long-safe-password"})
    assert result.status_code == 201
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_conversation_persists_grounded_references_and_is_private(client: TestClient):
    owner = auth(client, "chat_owner")
    other = auth(client, "chat_other")
    created = client.post("/api/chat/conversations", headers=owner)
    assert created.status_code == 200
    conversation_id = created.json()["id"]

    reply = client.post(f"/api/chat/conversations/{conversation_id}/messages", headers=owner, json={"content": "How can I check in with a quiet teammate?"})
    assert reply.status_code == 200
    assert reply.json()["role"] == "assistant"
    assert {"type": "scenario", "id": "quiet-teammate", "title": "A quiet teammate"} in reply.json()["references"]
    assert all(reference["type"] in {"lesson", "scenario"} for reference in reply.json()["references"])
    history = client.get(f"/api/chat/conversations/{conversation_id}", headers=owner).json()
    assert [message["role"] for message in history["messages"]] == ["user", "assistant"]
    assert client.get(f"/api/chat/conversations/{conversation_id}", headers=other).status_code == 404
    assert client.get("/api/chat/conversations", headers=other).json() == []


def test_chat_requires_auth_and_rejects_empty_messages(client: TestClient):
    assert client.post("/api/chat/conversations").status_code == 401
    owner = auth(client, "chat_validation")
    conversation = client.post("/api/chat/conversations", headers=owner).json()
    assert client.post(f"/api/chat/conversations/{conversation['id']}/messages", headers=owner, json={"content": "  "}).status_code == 422
