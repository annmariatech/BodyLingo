from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class CompletedLesson(Base):
    """Record a lesson completed by a learner."""

    __tablename__ = "completed_lessons"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "lesson_id",
            name="uq_completed_lesson_user_lesson",
        ),
        CheckConstraint(
            "xp_awarded >= 0",
            name="ck_completed_lesson_nonnegative_xp",
        ),
    )

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

    lesson_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    xp_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )