"""Synchronous SQLAlchemy configuration and request-scoped sessions."""

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class shared by persistent SQLAlchemy models."""


load_dotenv(Path(__file__).with_name(".env"))


def database_url() -> str:
    """Use PostgreSQL when configured; keep a local SQLite fallback for setup."""
    return os.getenv("DATABASE_URL", "").strip() or "sqlite:///./bodylingo.db"


def _make_engine():
    url = database_url()
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield and reliably close a database session for one request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
