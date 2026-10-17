"""Authentication API tests using an isolated in-memory SQLite database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import user  # noqa: F401


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-one-test-secret-key-at-least-32-chars")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        session = test_sessions()
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


def registration_payload(**overrides):
    return {
        "username": "ann_test",
        "email": "ann@example.com",
        "password": "a-long-safe-password",
        **overrides,
    }


def test_registration_hashes_password_and_returns_bearer_token(client: TestClient) -> None:
    response = client.post("/api/auth/register", json=registration_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["username"] == "ann_test"
    assert body["user"]["email"] == "ann@example.com"
    assert "password" not in body["user"]


def test_duplicate_email_or_username_is_rejected(client: TestClient) -> None:
    assert client.post("/api/auth/register", json=registration_payload()).status_code == 201

    duplicate = client.post(
        "/api/auth/register", json=registration_payload(username="another", email="ANN@example.com")
    )
    assert duplicate.status_code == 409


@pytest.mark.parametrize("identifier", ["ann_test", "ann@example.com"])
def test_login_accepts_username_or_email(client: TestClient, identifier: str) -> None:
    client.post("/api/auth/register", json=registration_payload())

    response = client.post(
        "/api/auth/login", json={"identifier": identifier, "password": "a-long-safe-password"}
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"]


def test_current_user_requires_a_valid_token_and_returns_profile(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401
    auth = client.post("/api/auth/register", json=registration_payload()).json()

    profile = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {auth['access_token']}"}
    )

    assert profile.status_code == 200
    assert profile.json()["id"] == auth["user"]["id"]
    assert profile.json()["email"] == "ann@example.com"


def test_logout_revokes_token(client: TestClient) -> None:
    auth = client.post("/api/auth/register", json=registration_payload()).json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    logout_response = client.post("/api/auth/logout", headers=headers)

    assert logout_response.status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_invalid_registration_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register", json=registration_payload(username="a", password="short")
    )

    assert response.status_code == 422
