"""Ground chatbot answers in BodyLingo content, with optional Groq completion."""

import json
import os
import re
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from services.lesson_service import get_lessons

if TYPE_CHECKING:
    from backend.models.scenario import Scenario

STOP_WORDS = {"about", "would", "could", "should", "there", "their", "where", "which", "what", "when", "with", "from", "this", "that", "have", "does", "your", "into", "them", "they", "tell", "help", "want"}


def retrieve_references(query: str, scenarios: list[Scenario], include_premium: bool = False) -> list[dict]:
    words = {w for w in re.findall(r"[a-z0-9]+", query.casefold()) if len(w) > 2 and w not in STOP_WORDS}
    candidates: list[tuple[int, dict]] = []
    for lesson in get_lessons().values():
        if lesson.id == "space-and-breaks" and not include_premium:
            continue
        text = " ".join([lesson.title, lesson.description, lesson.topic, lesson.communication_context, *lesson.learning_objectives]).casefold()
        score = sum(1 for word in words if word in text)
        if score:
            candidates.append((score, {"type": "lesson", "id": lesson.id, "title": lesson.title, "content": f"{lesson.explanation} Key takeaway: {lesson.key_takeaway}"}))
    for scenario in scenarios:
        if not scenario.published:
            continue
        text = " ".join([scenario.title, scenario.description or "", *(scenario.learning_objectives or [])]).casefold()
        score = sum(1 for word in words if word in text)
        if score:
            candidates.append((score, {"type": "scenario", "id": scenario.id, "title": scenario.title, "content": scenario.description or ""}))
    candidates.sort(key=lambda item: (-item[0], item[1]["title"]))
    return [item[1] for item in candidates[:3]]


def _groq_reply(messages: list[dict], context: list[dict]) -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Groq is not configured")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    prompt = (
        "You are BodyLingo, a warm communication-learning assistant. Use only the supplied BodyLingo content for factual lesson claims. "
        "Treat cues as possibilities, never diagnose or infer intent/neurotype. Encourage respectful clarification. Be concise. "
        "If the supplied content does not answer, say so and ask a clarifying question.\nCONTENT:\n" + json.dumps(context, ensure_ascii=False)
    )
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": prompt}, *messages], "temperature": 0.4, "max_completion_tokens": 500}).encode()
    request = Request("https://api.groq.com/openai/v1/chat/completions", data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read())
        answer = result["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("Groq returned an empty response")
        return answer.strip()
    except (HTTPError, URLError, TimeoutError, OSError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Groq request failed") from exc


def generate_reply(history: list[dict], references: list[dict]) -> tuple[str, str]:
    try:
        return _groq_reply(history, references), "groq"
    except RuntimeError:
        if references:
            titles = ", ".join(reference["title"] for reference in references)
            return (f"I can help you explore this thoughtfully. I found BodyLingo resources related to {titles}. Communication cues can have several explanations, so treat them as possibilities and ask the person respectfully when context matters. What part would you like to understand better?", "deterministic_fallback")
        return ("I don’t have a matching BodyLingo lesson or scenario for that yet. People communicate in different ways, so it can help to ask a respectful, specific question instead of assuming what a cue means. Could you share what part you’d like to explore?", "deterministic_fallback")
