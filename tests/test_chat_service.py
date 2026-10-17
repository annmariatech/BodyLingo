from services import chat_service


def test_groq_provider_receives_grounded_content(monkeypatch):
    monkeypatch.setattr(chat_service, "_groq_reply", lambda history, references: "A mocked, grounded answer")
    reply, provider = chat_service.generate_reply([{"role": "user", "content": "question"}], [{"title": "Lesson"}])
    assert (reply, provider) == ("A mocked, grounded answer", "groq")


def test_missing_provider_uses_safe_fallback(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    reply, provider = chat_service.generate_reply([{"role": "user", "content": "question"}], [])
    assert provider == "deterministic_fallback"
    assert "don’t have a matching" in reply
    assert "diagnos" not in reply.casefold()
