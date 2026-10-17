from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class ScenarioResponse(Base):
    """Record a learner's choice during a scenario session."""

    __tablename__ = "scenario_responses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scenario_sessions.id"),
        nullable=False,
        index=True,
    )

    node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    choice_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    next_node_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )