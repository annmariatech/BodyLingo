"""Safe lesson explanations with a deterministic fallback.

No external provider is configured in this implementation, so requests are
answered from local lesson content and are explicitly marked as fallbacks.
"""

from models.lesson import ExplanationRequest, ExplanationResponse, Lesson


def explain_lesson(
    lesson: Lesson, request: ExplanationRequest
) -> ExplanationResponse:
    """Build a predictable explanation without making an external API call."""
    example = lesson.examples[0] if lesson.examples else None
    example_text = (
        f"{example['situation']} {example['possible_interpretation']}"
        if example
        else lesson.key_takeaway
    )
    context_note = (
        f" In the context you shared ({request.context.strip()}), use this as a "
        "possibility to consider rather than a conclusion."
        if request.context
        else ""
    )
    preference_note = ""
    if request.profile_preferences:
        preferences = "; ".join(
            f"{key}: {value}" for key, value in request.profile_preferences.items()
        )
        preference_note = (
            f" You shared these communication preferences ({preferences}); "
            "you can use them to decide what kind of clarification feels comfortable."
        )

    return ExplanationResponse(
        explanation=(
            f"For “{request.question.strip()},” {lesson.explanation}"
            f"{context_note}{preference_note}"
        ),
        example=example_text,
        alternative_interpretations=[
            "The cue may have more than one explanation, including factors unrelated to you.",
            "The person's own words or a respectful check-in may provide clearer context.",
        ],
        communication_tip=(
            "If it would help, ask a neutral question such as, “Would you like to "
            "tell me what you mean?” and respect the answer."
        ),
        reminder=(
            "A single communication cue cannot establish someone's intent, feelings, "
            "or neurotype. People communicate differently; ask respectfully instead "
            "of assuming."
        ),
        provider="deterministic_fallback",
        used_fallback=True,
    )
