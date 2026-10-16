import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.base import Base
from backend.models.scenario import Scenario
from backend.models.scenario_session import ScenarioSession
from backend.models.scenario_response import ScenarioResponse
from backend.models.user_progress import UserProgress
from backend.models.completed_lesson import CompletedLesson


@pytest.fixture
def db_session():
    """Create an isolated SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_all_five_tables_are_created(db_session):
    table_names = set(inspect(db_session.get_bind()).get_table_names())

    assert table_names == {
        "scenarios",
        "scenario_sessions",
        "scenario_responses",
        "user_progress",
        "completed_lessons",
    }


def test_scenario_session_and_response_can_be_saved(db_session):
    scenario = Scenario(
        id="team-communication",
        title="Team communication",
        start_node_id="start",
        nodes={
            "start": {
                "prompt": "How would you respond?",
                "choices": [],
            }
        },
        published=True,
    )
    db_session.add(scenario)
    db_session.flush()

    scenario_session = ScenarioSession(
        user_id="test-user",
        scenario_id="team-communication",
        current_node_id="start",
        simulation_type="hr",
    )
    db_session.add(scenario_session)
    db_session.flush()

    response = ScenarioResponse(
        session_id=scenario_session.id,
        node_id="start",
        choice_id="ask-gently",
        next_node_id=None,
        feedback="A respectful response.",
    )
    db_session.add(response)
    db_session.commit()

    saved_response = db_session.get(ScenarioResponse, response.id)
    assert saved_response is not None
    assert saved_response.choice_id == "ask-gently"
    assert saved_response.session_id == scenario_session.id


def test_completed_lesson_is_unique_per_user(db_session):
    first = CompletedLesson(
        user_id="test-user",
        lesson_id="lesson-1",
        xp_awarded=10,
    )
    db_session.add(first)
    db_session.commit()

    duplicate = CompletedLesson(
        user_id="test-user",
        lesson_id="lesson-1",
        xp_awarded=10,
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_progress_rejects_negative_xp(db_session):
    db_session.add(
        UserProgress(
            user_id="test-user",
            total_xp=-1,
            current_streak=0,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_completed_lesson_rejects_negative_xp(db_session):
    db_session.add(
        CompletedLesson(
            user_id="test-user",
            lesson_id="lesson-1",
            xp_awarded=-5,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()