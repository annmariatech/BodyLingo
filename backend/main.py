"""FastAPI application entry point for BodyLingo."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# The supported local command runs `uvicorn main:app` from backend/. Scenario
# models use the `backend.models` package path, so also expose the repository
# root when the app is launched from that working directory.
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from routers.auth import router as auth_router
from routers.lessons import router as lessons_router
from routers.learning import router as learning_router
from routers.scenarios import router as scenarios_router
from routers.chat import router as chat_router
from routers.forum import router as forum_router
import models.chat  # noqa: F401; register chatbot tables with Base.metadata
import models.learning  # noqa: F401; register learning tables for test and CLI metadata


def _configured_origins() -> list[str]:
    """Read allowed browser origins, defaulting to common local dev servers."""
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    # Wildcard origins are only useful for local experiments. Refuse them in
    # production so credentials or private API responses are not exposed broadly.
    if os.getenv("APP_ENV", "development").lower() == "production":
        origins = [origin for origin in origins if origin != "*"]

    return origins


app = FastAPI(
    title="BodyLingo API",
    description="Backend API for BodyLingo learning experiences.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_configured_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(scenarios_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(forum_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Report that the API process is running without contacting dependencies."""
    return {"status": "ok"}
