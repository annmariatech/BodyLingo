"""Read and validate lesson content stored in the local JSON data file."""

import json
from functools import lru_cache
from pathlib import Path

from models.lesson import Lesson

LESSONS_PATH = Path(__file__).resolve().parents[1] / "data" / "lessons.json"


@lru_cache(maxsize=1)
def get_lessons() -> dict[str, Lesson]:
    """Load lessons once per process and validate the content with Pydantic."""
    with LESSONS_PATH.open(encoding="utf-8") as lesson_file:
        raw_lessons = json.load(lesson_file)

    lessons = [Lesson.model_validate(item) for item in raw_lessons]
    return {lesson.id: lesson for lesson in lessons}
