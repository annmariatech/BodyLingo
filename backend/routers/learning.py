"""Authenticated onboarding, recommendations, quizzes and progress endpoints."""

from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import CurrentUser
from models.learning import LessonAttempt, LessonCompletion, QuestionReview
from models.user import User
from schemas.learning import AttemptRequest, AttemptResponse, PreferencesUpdate, ProgressResponse, Question
from services.lesson_service import get_lessons
from services.question_bank import QUESTIONS, answer_for, questions_for
from routers.lessons import PREMIUM_LESSONS

router = APIRouter(prefix="/learning", tags=["learning"])
TOPIC_ALIASES = {
    "facial expressions": "facial expressions",
    "tone of voice": "tone of voice",
    "eye contact": "eye contact",
    "personal space and breaks": "personal space and breaks",
    "gestures and culture": "gestures",
    "clarifying needs": "clarification",
}


@router.get("/preferences", response_model=PreferencesUpdate)
def get_preferences(user: CurrentUser) -> dict:
    return user.preferences or {}


@router.put("/preferences", response_model=PreferencesUpdate)
def update_preferences(payload: PreferencesUpdate, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    user.preferences = payload.model_dump()
    db.commit()
    db.refresh(user)
    return user.preferences


@router.get("/recommendations")
def recommendations(user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    preferences = user.preferences or {}
    topics = {TOPIC_ALIASES.get(item.casefold(), item.casefold()) for item in preferences.get("topics", [])}
    situations = {item.casefold() for item in preferences.get("situations", [])}
    completed = set(db.scalars(select(LessonCompletion.lesson_id).where(LessonCompletion.user_id == user.id)))
    ranked = []
    for lesson in get_lessons().values():
        if lesson.id in PREMIUM_LESSONS and not user.is_premium:
            locked = True
        else:
            locked = False
        topic_match = lesson.topic.casefold() in topics or any(
            topic in lesson.topic.casefold() for topic in topics
        )
        context_words = set(lesson.communication_context.casefold().replace(",", " ").replace(".", " ").split())
        situation_match = any(
            bool({word for word in situation.split() if len(word) > 4} & context_words)
            for situation in situations
        )
        score = (4 if topic_match else 0) + (2 if situation_match else 0) + (3 if lesson.id not in completed else -3)
        ranked.append((score, lesson.id not in completed, lesson, locked, topic_match, situation_match))
    ranked.sort(key=lambda item: (item[0], item[1], item[2].title), reverse=True)
    return [
        {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "topic": lesson.topic,
            "difficulty": lesson.difficulty,
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
            "learning_objectives": lesson.learning_objectives,
            "communication_context": lesson.communication_context,
            "is_premium": lesson.id in PREMIUM_LESSONS,
            "locked": locked,
            "completed": lesson.id in completed,
            "recommendation_reason": "Matches a topic you chose" if topic_match else ("Matches a situation you chose" if situation_match else ("Continue your learning path" if lesson.id not in completed else "Review a completed topic")),
        }
        for _, _, lesson, locked, topic_match, situation_match in ranked
    ]


def _require_lesson(lesson_id: str, user: User):
    lesson = get_lessons().get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson_id in PREMIUM_LESSONS and not user.is_premium:
        raise HTTPException(status_code=403, detail="Premium access is required for this lesson")
    return lesson


@router.get("/lessons/{lesson_id}/questions", response_model=list[Question])
def lesson_questions(lesson_id: str, user: CurrentUser) -> list[dict]:
    _require_lesson(lesson_id, user)
    return questions_for(lesson_id)


@router.get("/reviews")
def reviews(user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    """List only this learner's scheduled questions, without answer keys."""
    now = datetime.now(timezone.utc)
    rows = db.scalars(select(QuestionReview).where(QuestionReview.user_id == user.id).order_by(QuestionReview.due_at)).all()
    lesson_titles = {lesson.id: lesson.title for lesson in get_lessons().values()}
    results = []
    for row in rows:
        lesson = get_lessons().get(row.lesson_id)
        if lesson is None or (row.lesson_id in PREMIUM_LESSONS and not user.is_premium):
            continue
        question = next((item for item in questions_for(row.lesson_id) if item["id"] == row.question_id), None)
        if question:
            due_at = row.due_at if row.due_at.tzinfo else row.due_at.replace(tzinfo=timezone.utc)
            results.append({
                "lesson_id": row.lesson_id,
                "lesson_title": lesson_titles[row.lesson_id],
                "question": question,
                "due_at": due_at,
                "is_due": due_at <= now,
            })
    return results


@router.post("/lessons/{lesson_id}/attempts/{question_id}", response_model=AttemptResponse)
def submit_attempt(
    lesson_id: str,
    question_id: str,
    payload: AttemptRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> AttemptResponse:
    _require_lesson(lesson_id, user)
    if payload.question_id != question_id:
        raise HTTPException(status_code=422, detail="Question ID does not match the URL")
    result = answer_for(lesson_id, question_id, payload.selected_option_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Question or option not found")
    correct, explanation = result
    now = datetime.now(timezone.utc)
    db.add(LessonAttempt(
        user_id=user.id,
        lesson_id=lesson_id,
        question_id=question_id,
        selected_option_id=payload.selected_option_id,
        is_correct=correct,
        attempted_at=now,
    ))
    db.flush()
    review = db.scalar(select(QuestionReview).where(
        QuestionReview.user_id == user.id,
        QuestionReview.lesson_id == lesson_id,
        QuestionReview.question_id == question_id,
    ))
    if not correct:
        if review is None:
            review = QuestionReview(user_id=user.id, lesson_id=lesson_id, question_id=question_id)
            db.add(review)
        review.interval_days = 1
        review.repetitions = 0
        review.due_at = now + timedelta(days=1)
    elif review is not None:
        review.repetitions += 1
        review.interval_days = 3 if review.repetitions == 1 else 7
        review.due_at = now + timedelta(days=review.interval_days)

    correct_question_ids = set(db.scalars(select(LessonAttempt.question_id).where(
        LessonAttempt.user_id == user.id,
        LessonAttempt.lesson_id == lesson_id,
        LessonAttempt.is_correct.is_(True),
    )))
    all_correct = {item[0] for item in QUESTIONS.get(lesson_id, [])}.issubset(correct_question_ids)
    completed = db.scalar(select(LessonCompletion).where(
        LessonCompletion.user_id == user.id, LessonCompletion.lesson_id == lesson_id
    ))
    if all_correct and completed is None:
        db.add(LessonCompletion(user_id=user.id, lesson_id=lesson_id))
    db.commit()
    return AttemptResponse(
        correct=correct,
        explanation=explanation,
        completed=all_correct,
        retry_due_at=(now + timedelta(days=1)) if not correct else (review.due_at if review else None),
    )


@router.get("/progress", response_model=ProgressResponse)
def progress(user: CurrentUser, db: Session = Depends(get_db)) -> ProgressResponse:
    now = datetime.now(timezone.utc)
    return ProgressResponse(
        completed_lessons=list(db.scalars(select(LessonCompletion.lesson_id).where(LessonCompletion.user_id == user.id))),
        attempts=db.scalar(select(func.count()).select_from(LessonAttempt).where(LessonAttempt.user_id == user.id)) or 0,
        correct_answers=db.scalar(select(func.count()).select_from(LessonAttempt).where(
            LessonAttempt.user_id == user.id, LessonAttempt.is_correct.is_(True)
        )) or 0,
        due_reviews=db.scalar(select(func.count()).select_from(QuestionReview).where(
            QuestionReview.user_id == user.id, QuestionReview.due_at <= now
        )) or 0,
        is_premium=user.is_premium,
    )


@router.post("/premium/demo")
def enable_demo_premium(user: CurrentUser, db: Session = Depends(get_db)) -> dict[str, bool]:
    if os.getenv("APP_ENV", "development").lower() == "production" or os.getenv("ENABLE_DEMO_PREMIUM") != "1":
        raise HTTPException(status_code=404, detail="Demo premium is disabled")
    user.is_premium = True
    db.commit()
    return {"is_premium": True}
