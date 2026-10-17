"""Lesson retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.lesson import (
    ExplanationRequest,
    ExplanationResponse,
    Lesson,
    LessonSummary,
)
from services.ai_service import explain_lesson
from services.lesson_service import get_lessons
from dependencies.auth import OptionalCurrentUser
from models.learning import LessonCompletion

PREMIUM_LESSONS = {"space-and-breaks"}

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonSummary])
async def list_lessons(user: OptionalCurrentUser, db: Session = Depends(get_db)) -> list[LessonSummary]:
    """List lesson metadata without returning the full lesson bodies."""
    completed = set()
    if user is not None:
        completed = set(db.scalars(select(LessonCompletion.lesson_id).where(LessonCompletion.user_id == user.id)))
    return [
        LessonSummary.model_validate({
            **lesson.model_dump(include=set(LessonSummary.model_fields)),
            "is_premium": lesson.id in PREMIUM_LESSONS,
            "locked": lesson.id in PREMIUM_LESSONS and not (user and user.is_premium),
            "completed": lesson.id in completed,
        })
        for lesson in get_lessons().values()
    ]


@router.get("/{lesson_id}", response_model=Lesson)
async def retrieve_lesson(lesson_id: str, user: OptionalCurrentUser) -> Lesson:
    """Return the complete content for one lesson."""
    lesson = get_lessons().get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson_id in PREMIUM_LESSONS and not (user and user.is_premium):
        raise HTTPException(status_code=403, detail="Premium access is required for this lesson")
    # The legacy knowledge check contains its answer for offline lesson rendering.
    # Never send the answer key to the browser; scoring happens server-side.
    safe_content = lesson.model_dump()
    check = safe_content.get("knowledge_check", {})
    if isinstance(check, dict):
        check.pop("answer", None)
    return Lesson.model_validate(safe_content)


@router.post("/{lesson_id}/explain", response_model=ExplanationResponse)
async def explain(lesson_id: str, request: ExplanationRequest) -> ExplanationResponse:
    """Explain a lesson concept using local content and a safe fallback."""
    lesson = get_lessons().get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return explain_lesson(lesson, request)
