"""Persistent learning attempts and spaced-repetition state."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LessonAttempt(Base):
    __tablename__ = "lesson_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(String(100), index=True)
    question_id: Mapped[str] = mapped_column(String(100))
    selected_option_id: Mapped[str] = mapped_column(String(100))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_completion_user_lesson"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(String(100))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class QuestionReview(Base):
    __tablename__ = "question_reviews"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", "question_id", name="uq_question_review_user_question"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(String(100))
    question_id: Mapped[str] = mapped_column(String(100))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
