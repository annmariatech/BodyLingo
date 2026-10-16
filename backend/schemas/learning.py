"""Validated learning preference, question, attempt and progress contracts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topics: list[str] = Field(default_factory=list, max_length=12)
    situations: list[str] = Field(default_factory=list, max_length=12)
    explanation_style: str = Field(default="balanced", max_length=40)
    communication_preferences: list[str] = Field(default_factory=list, max_length=12)
    cultural_contexts: list[str] = Field(default_factory=list, max_length=12)
    skipped: bool = False


class Option(BaseModel):
    id: str
    text: str


class Question(BaseModel):
    id: str
    prompt: str
    options: list[Option]
    explanation: str


class AttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1, max_length=100)
    selected_option_id: str = Field(min_length=1, max_length=100)


class AttemptResponse(BaseModel):
    correct: bool
    explanation: str
    completed: bool
    retry_due_at: datetime | None = None


class ProgressResponse(BaseModel):
    completed_lessons: list[str]
    attempts: int
    correct_answers: int
    due_reviews: int
    is_premium: bool
