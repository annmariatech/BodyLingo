"""Validated response models for lesson content."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LessonSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    topic: str
    difficulty: str
    estimated_duration_minutes: int = Field(gt=0)
    learning_objectives: list[str]
    communication_context: str
    is_premium: bool = False
    locked: bool = False
    completed: bool = False


class Lesson(LessonSummary):
    introduction: str
    communication_cue: str
    explanation: str
    examples: list[dict[str, str]]
    knowledge_check: dict[str, str | list[str]]
    key_takeaway: str


class ExplanationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=1000)
    context: str | None = Field(default=None, max_length=1000)
    profile_preferences: dict[str, str] | None = None

    @field_validator("question", "context")
    @classmethod
    def reject_blank_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be empty or whitespace only")
        return value

    @field_validator("profile_preferences")
    @classmethod
    def bound_profile_preferences(
        cls, value: dict[str, str] | None
    ) -> dict[str, str] | None:
        if value is None:
            return value
        if len(value) > 10:
            raise ValueError("profile_preferences may contain at most 10 entries")
        for key, preference in value.items():
            if not key.strip() or not preference.strip():
                raise ValueError("profile preference keys and values must not be blank")
            if len(key) > 80 or len(preference) > 300:
                raise ValueError("profile preference keys or values are too long")
        return value


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: str
    example: str
    alternative_interpretations: list[str]
    communication_tip: str
    reminder: str
    provider: str
    used_fallback: bool
