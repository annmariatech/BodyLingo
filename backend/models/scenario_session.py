from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class ScenarioSession(Base):
    """Track an individual learner's progress through a scenario."""

    __tablename__ = "scenario_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    scenario_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("scenarios.id"),
        nullable=False,
        index=True,
    )

    current_node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    simulation_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="general",
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )