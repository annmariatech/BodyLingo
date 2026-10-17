import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.models.base import Base
from backend.models.scenario import Scenario
from backend.models.scenario_session import ScenarioSession
from backend.schemas.scenario import ScenarioDetailResponse, ScenarioListResponse
from backend.services.scenario_service import (
    ScenarioNotFoundError,
    get_scenario_detail,
    list_scenarios,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    with TestingSession() as session:
        yield session

    engine.dispose()


def add_scenario(db: Session, *, published: bool = True) -> Scenario:
    scenario = Scenario(
        id="team_meeting_01",
        title="Team meeting",
        description="Respond to a teammate who becomes quiet.",
        start_node_id="step_1",
        published=published,
        nodes={
            "step_1": {
                "prompt": "Your teammate becomes quiet. What do you do?",
                "choices": [
                    {
                        "id": "a",
                        "label": "Ask privately if they need a break",
                        "next_node_id": "step_2",
                        "feedback": "A gentle question invites conversation.",
                    },
                    {
                        "id": "b",
                        "label": "Demand an immediate explanation",
                        "next_node_id": None,
                        "feedback": "Consider giving them space.",
                    },
                ],
            },
            "step_2": {
                "prompt": "They ask for a quiet place. What next?",
                "choices": [
                    {
                        "id": "c",
                        "label": "Help them find a quiet space",
                        "next_node_id": None,
                        "feedback": "You respected their needs.",
                    }
                ],
            },
        },
    )

    db.add(scenario)
    db.commit()
    return scenario


def test_list_scenarios_returns_published_scenarios(db):
    add_scenario(db)

    result = list_scenarios(db)

    assert isinstance(result, ScenarioListResponse)
    assert len(result.scenarios) == 1
    assert result.scenarios[0].id == "team_meeting_01"


def test_list_scenarios_hides_unpublished_scenarios(db):
    add_scenario(db, published=False)

    result = list_scenarios(db)

    assert result.scenarios == []


def test_get_scenario_detail_returns_initial_step(db):
    add_scenario(db)

    result = get_scenario_detail(
        db,
        scenario_id="team_meeting_01",
        user_id="learner_1",
    )

    assert isinstance(result, ScenarioDetailResponse)
    assert result.scenario_id == "team_meeting_01"
    assert result.current_step == "step_1"
    assert result.prompt == "Your teammate becomes quiet. What do you do?"
    assert result.choices[0].id == "a"
    assert result.choices[0].text == (
        "Ask privately if they need a break"
    )


def test_get_scenario_detail_resumes_existing_session(db):
    add_scenario(db)

    db.add(
        ScenarioSession(
            id="session_001",
            user_id="learner_1",
            scenario_id="team_meeting_01",
            current_node_id="step_2",
            simulation_type="general",
            is_completed=False,
        )
    )
    db.commit()

    result = get_scenario_detail(
        db,
        scenario_id="team_meeting_01",
        user_id="learner_1",
    )

    assert result.current_step == "step_2"
    assert result.prompt == "They ask for a quiet place. What next?"


def test_get_scenario_detail_rejects_unknown_scenario(db):
    with pytest.raises(ScenarioNotFoundError):
        get_scenario_detail(
            db,
            scenario_id="missing_scenario",
            user_id="learner_1",
        )

def test_respond_to_scenario_saves_response_and_advances(db):
    from sqlalchemy import select

    from backend.models.scenario_response import ScenarioResponse
    from backend.services.scenario_service import respond_to_scenario

    add_scenario(db)

    result = respond_to_scenario(
        db,
        scenario_id="team_meeting_01",
        user_id="learner_1",
        current_step="step_1",
        choice_id="a",
    )

    assert result.scenario_id == "team_meeting_01"
    assert result.feedback == "A gentle question invites conversation."
    assert result.current_step == "step_2"
    assert result.prompt == "They ask for a quiet place. What next?"
    assert result.completed is False

    learner_session = db.scalar(
        select(ScenarioSession).where(
            ScenarioSession.user_id == "learner_1",
            ScenarioSession.scenario_id == "team_meeting_01",
        )
    )
    assert learner_session is not None
    assert learner_session.current_node_id == "step_2"
    assert learner_session.is_completed is False

    saved_response = db.scalar(
        select(ScenarioResponse).where(
            ScenarioResponse.session_id == learner_session.id
        )
    )
    assert saved_response is not None
    assert saved_response.choice_id == "a"
    assert saved_response.next_node_id == "step_2"


def test_respond_to_scenario_marks_session_completed(db):
    from sqlalchemy import select

    from backend.models.scenario_response import ScenarioResponse
    from backend.services.scenario_service import respond_to_scenario

    add_scenario(db)

    learner_session = ScenarioSession(
        id="session_final",
        user_id="learner_1",
        scenario_id="team_meeting_01",
        current_node_id="step_2",
        simulation_type="general",
        is_completed=False,
    )
    db.add(learner_session)
    db.commit()

    result = respond_to_scenario(
        db,
        scenario_id="team_meeting_01",
        user_id="learner_1",
        current_step="step_2",
        choice_id="c",
    )

    assert result.completed is True
    assert result.current_step is None
    assert result.prompt is None
    assert result.choices == []

    db.refresh(learner_session)
    assert learner_session.is_completed is True
    assert learner_session.completed_at is not None

    saved_response = db.scalar(
        select(ScenarioResponse).where(
            ScenarioResponse.session_id == learner_session.id
        )
    )
    assert saved_response is not None
    assert saved_response.choice_id == "c"
    assert saved_response.next_node_id is None


def test_respond_to_scenario_rejects_invalid_choice(db):
    from sqlalchemy import select

    from backend.models.scenario_response import ScenarioResponse
    from backend.services.scenario_service import (
        ScenarioChoiceInvalidError,
        respond_to_scenario,
    )

    add_scenario(db)

    with pytest.raises(ScenarioChoiceInvalidError):
        respond_to_scenario(
            db,
            scenario_id="team_meeting_01",
            user_id="learner_1",
            current_step="step_1",
            choice_id="not_a_real_choice",
        )

    assert db.scalars(select(ScenarioSession)).all() == []
    assert db.scalars(select(ScenarioResponse)).all() == []


def test_respond_to_scenario_rejects_stale_step(db):
    from sqlalchemy import select

    from backend.models.scenario_response import ScenarioResponse
    from backend.services.scenario_service import (
        ScenarioStepConflictError,
        respond_to_scenario,
    )

    add_scenario(db)

    db.add(
        ScenarioSession(
            id="session_stale",
            user_id="learner_1",
            scenario_id="team_meeting_01",
            current_node_id="step_2",
            simulation_type="general",
            is_completed=False,
        )
    )
    db.commit()

    with pytest.raises(ScenarioStepConflictError):
        respond_to_scenario(
            db,
            scenario_id="team_meeting_01",
            user_id="learner_1",
            current_step="step_1",
            choice_id="a",
        )

    saved_responses = db.scalars(select(ScenarioResponse)).all()
    assert saved_responses == []
