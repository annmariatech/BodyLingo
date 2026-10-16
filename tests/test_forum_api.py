"""Forum feed filtering and safe topic classification tests."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models.chat  # noqa: F401
import models.learning  # noqa: F401
import models.user  # noqa: F401
from services import forum_service


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "forum-test-secret-key-at-least-32-characters")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    forum_service._groq_tags.cache_clear()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

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
    Base.metadata.drop_all(engine)
    engine.dispose()
    forum_service._groq_tags.cache_clear()


def auth(client: TestClient) -> dict[str, str]:
    result = client.post("/api/auth/register", json={"username": "forum_reader", "email": "forum@example.com", "password": "a-long-safe-password"})
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_forum_feed_is_fictional_read_only_and_searchable(client: TestClient):
    headers = auth(client)
    assert client.get("/api/forum/posts").status_code == 401
    feed = client.get("/api/forum/posts", headers=headers).json()
    assert len(feed["posts"]) == 8
    assert all(post["fictional"] is True and post["topic_tags"] for post in feed["posts"])
    assert feed["classification"] == "deterministic_fallback"

    work = client.get("/api/forum/posts", headers=headers, params={"category": "Work & study"}).json()
    assert len(work["posts"]) == 2
    assert all(post["category"] == "Work & study" for post in work["posts"])

    searched = client.get("/api/forum/posts", headers=headers, params={"query": "eye contact"}).json()
    assert [post["id"] for post in searched["posts"]] == ["eye-contact-preferences"]
    assert client.get("/api/forum/posts", headers=headers, params={"query": "no such topic"}).json()["posts"] == []
    assert client.get("/api/forum/posts", headers=headers, params={"category": "Unknown"}).json()["posts"] == []


def test_groq_topic_tags_are_validated_and_fallback_is_deterministic(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GROQ_API_KEY", "mock-key")
    forum_service._groq_tags.cache_clear()

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            payload = {"choices": [{"message": {"content": json.dumps({"tags": ["culture", "invented-tag"]})}}]}
            return json.dumps(payload).encode()

    monkeypatch.setattr(forum_service, "urlopen", lambda *args, **kwargs: MockResponse())
    tags, method = forum_service.classify_post({"title": "Gesture context", "excerpt": "An unfamiliar gesture."})
    assert (tags, method) == (["culture"], "groq")

    forum_service._groq_tags.cache_clear()
    monkeypatch.delenv("GROQ_API_KEY")
    fallback_tags, fallback_method = forum_service.classify_post({"title": "Eye contact preferences", "excerpt": "Different listening styles."})
    assert fallback_method == "deterministic_fallback"
    assert fallback_tags
