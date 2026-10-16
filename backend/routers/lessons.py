"""Lesson retrieval endpoints."""

from fastapi import APIRouter, HTTPException

from models.lesson import (
    ExplanationRequest,
    ExplanationResponse,
    Lesson,
    LessonSummary,
)
from services.ai_service import explain_lesson
from services.lesson_service import get_lessons

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonSummary])
async def list_lessons() -> list[LessonSummary]:
    """List lesson metadata without returning the full lesson bodies."""
    return [LessonSummary.model_validate(lesson) for lesson in get_lessons().values()]


@router.get("/{lesson_id}", response_model=Lesson)
async def retrieve_lesson(lesson_id: str) -> Lesson:
    """Return the complete content for one lesson."""
    lesson = get_lessons().get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/{lesson_id}/explain", response_model=ExplanationResponse)
async def explain(lesson_id: str, request: ExplanationRequest) -> ExplanationResponse:
    """Explain a lesson concept using local content and a safe fallback."""
    lesson = get_lessons().get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return explain_lesson(lesson, request)
