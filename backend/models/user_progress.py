from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class UserProgress(Base):
    """Store a learner's overall BodyLingo progress."""

    __tablename__ = "user_progress"

    __table_args__ = (
        CheckConstraint("total_xp >= 0", name="ck_progress_nonnegative_xp"),
        CheckConstraint(
            "current_streak >= 0",
            name="ck_progress_nonnegative_streak",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    total_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    current_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_active_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )