"""Read-only sample feed, searchable labels and optional Groq topic tagging."""

import json
import os
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

POSTS_PATH = Path(__file__).resolve().parents[1] / "data" / "forum_posts.json"
CATEGORIES = ["Everyday communication", "Work & study", "Culture & context", "Access & wellbeing"]
ALLOWED_TAGS = ["clarification", "workplace", "boundaries", "nonverbal cues", "context", "neurodiversity", "accessibility", "culture", "sensory needs", "relationships"]
TAG_KEYWORDS = {
    "clarification": {"clarif", "ask", "check", "mean", "context"},
    "workplace": {"meeting", "teammate", "work", "group", "study"},
    "boundaries": {"choice", "respect", "pressure", "comfort", "prefer"},
    "nonverbal cues": {"quiet", "tone", "gesture", "eye", "listen", "message"},
    "context": {"context", "situation", "meaning", "culture", "timing"},
    "neurodiversity": {"neurodiversity", "different", "style", "attention"},
    "accessibility": {"option", "access", "pause", "note", "break", "listen"},
    "culture": {"culture", "local", "gesture", "unfamiliar"},
    "sensory needs": {"sensory", "quiet", "break", "overload", "pressure"},
    "relationships": {"person", "conversation", "message", "respect", "ask"},
}


@lru_cache(maxsize=1)
def get_seed_posts() -> tuple[dict, ...]:
    with POSTS_PATH.open(encoding="utf-8") as file:
        posts = json.load(file)
    return tuple(posts)


def deterministic_tags(title: str, excerpt: str) -> list[str]:
    text = f"{title} {excerpt}".casefold()
    ranked = []
    for tag, keywords in TAG_KEYWORDS.items():
        score = sum(1 for word in keywords if word in text)
        if score:
            ranked.append((score, tag))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [tag for _, tag in ranked[:3]] or ["context"]


@lru_cache(maxsize=128)
def _groq_tags(title: str, excerpt: str) -> tuple[str, ...]:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Groq is not configured")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": f"Assign 1 to 3 topic tags from this exact allowed list: {', '.join(ALLOWED_TAGS)}. Return only JSON in the form {{\"tags\":[...]}}. Do not infer personal traits."},
            {"role": "user", "content": json.dumps({"title": title, "excerpt": excerpt})},
        ],
        "temperature": 0,
        "max_completion_tokens": 100,
        "response_format": {"type": "json_object"},
    }).encode()
    request = Request("https://api.groq.com/openai/v1/chat/completions", data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=8) as response:
            data = json.loads(response.read())
        content = data["choices"][0]["message"]["content"]
        tags = json.loads(content).get("tags")
        if not isinstance(tags, list):
            raise RuntimeError("Invalid topic tags")
        checked = tuple(dict.fromkeys(tag for tag in tags if isinstance(tag, str) and tag in ALLOWED_TAGS))
        if not 1 <= len(checked) <= 3:
            raise RuntimeError("No valid topic tags")
        return checked
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Topic classification failed") from exc


def classify_post(post: dict) -> tuple[list[str], str]:
    try:
        return list(_groq_tags(post["title"], post["excerpt"])), "groq"
    except RuntimeError:
        return deterministic_tags(post["title"], post["excerpt"]), "deterministic_fallback"


def search_posts(query: str = "", category: str = "") -> dict:
    normalized_query = query.casefold().strip()
    if category and category not in CATEGORIES:
        return {"posts": [], "categories": CATEGORIES, "classification": "deterministic_fallback"}
    matches = []
    methods = set()
    for source in get_seed_posts():
        if category and source["category"] != category:
            continue
        source_haystack = " ".join([source["title"], source["excerpt"], source["category"], *source["topic_tags"]]).casefold()
        if normalized_query and normalized_query not in source_haystack:
            continue
        tags, method = classify_post(source)
        item = {**source, "topic_tags": tags}
        methods.add(method)
        matches.append(item)
    classification = "groq" if methods == {"groq"} else "deterministic_fallback"
    return {"posts": matches, "categories": CATEGORIES, "classification": classification}
