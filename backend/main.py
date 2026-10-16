"""FastAPI application entry point for BodyLingo."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.lessons import router as lessons_router


def _configured_origins() -> list[str]:
    """Read allowed browser origins, defaulting to common local dev servers."""
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(lessons_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Report that the API process is running without contacting dependencies."""
    return {"status": "ok"}
