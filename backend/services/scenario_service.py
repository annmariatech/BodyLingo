from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.scenario import Scenario
from backend.models.scenario_response import ScenarioResponse
from backend.models.scenario_session import ScenarioSession
from backend.schemas.scenario import (
    ScenarioChoiceResponse,
    ScenarioDetailResponse,
    ScenarioListResponse,
    ScenarioRespondResponse,
    ScenarioStepResponse,
    ScenarioSummaryResponse,
)
from backend.services.scenario_engine import (
    ScenarioChoiceNotFoundError,
    get_scenario_step,
    submit_scenario_choice,
)


class ScenarioNotFoundError(LookupError):
    """Raised when a scenario is missing or unavailable."""


class ScenarioChoiceInvalidError(ValueError):
    """Raised when a choice does not exist at the submitted step."""


class ScenarioStepConflictError(ValueError):
    """Raised when the submitted step differs from the learner's current step."""


def _scenario_definition(scenario: Scenario) -> dict[str, Any]:
    """Convert a database scenario into the format used by the engine."""
    return {
        "id": scenario.id,
        "title": scenario.title,
        "start_node_id": scenario.start_node_id,
        "nodes": scenario.nodes,
    }


def _public_step(
    scenario: Scenario,
    node_id: str,
) -> ScenarioStepResponse:
    """Convert an internal scenario node into the public API format."""
    step = get_scenario_step(
        _scenario_definition(scenario),
        node_id,
    )

    return ScenarioStepResponse(
        scenario_id=step["scenario_id"],
        current_step=step["node_id"],
        prompt=step["prompt"],
        choices=[
            ScenarioChoiceResponse(
                id=choice["id"],
                text=choice["label"],
            )
            for choice in step["choices"]
        ],
    )


def list_scenarios(db: Session) -> ScenarioListResponse:
    """Return published scenarios, ordered by title."""
    statement = (
        select(Scenario)
        .where(Scenario.published.is_(True))
        .order_by(Scenario.title)
    )

    scenarios = db.scalars(statement).all()

    return ScenarioListResponse(
        scenarios=[
            ScenarioSummaryResponse(
                id=scenario.id,
                title=scenario.title,
                description=scenario.description,
            )
            for scenario in scenarios
        ]
    )


def get_scenario_detail(
    db: Session,
    *,
    scenario_id: str,
    user_id: str,
) -> ScenarioDetailResponse:
    """Return the initial step or resume the learner's unfinished session."""
    statement = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.published.is_(True),
    )

    scenario = db.scalar(statement)

    if scenario is None:
        raise ScenarioNotFoundError(
            f"Scenario '{scenario_id}' was not found."
        )

    session_statement = (
        select(ScenarioSession)
        .where(
            ScenarioSession.user_id == user_id,
            ScenarioSession.scenario_id == scenario_id,
            ScenarioSession.is_completed.is_(False),
        )
        .order_by(ScenarioSession.started_at.desc())
        .limit(1)
    )

    learner_session = db.scalar(session_statement)

    current_node_id = (
        learner_session.current_node_id
        if learner_session is not None
        else scenario.start_node_id
    )

    step = _public_step(scenario, current_node_id)

    return ScenarioDetailResponse(
        scenario_id=step.scenario_id,
        current_step=step.current_step,
        prompt=step.prompt,
        choices=step.choices,
    )


def respond_to_scenario(
    db: Session,
    *,
    scenario_id: str,
    user_id: str,
    current_step: str,
    choice_id: str,
) -> ScenarioRespondResponse:
    """Process a learner's choice and persist the session and response."""
    scenario_statement = select(Scenario).where(
        Scenario.id == scenario_id,
        Scenario.published.is_(True),
    )

    scenario = db.scalar(scenario_statement)

    if scenario is None:
        raise ScenarioNotFoundError(
            f"Scenario '{scenario_id}' was not found."
        )

    # Find this learner's latest unfinished session.
    session_statement = (
        select(ScenarioSession)
        .where(
            ScenarioSession.user_id == user_id,
            ScenarioSession.scenario_id == scenario_id,
            ScenarioSession.is_completed.is_(False),
        )
        .order_by(ScenarioSession.started_at.desc())
        .limit(1)
    )

    learner_session = db.scalar(session_statement)

    # Validate that the learner is answering the expected step.
    if learner_session is not None:
        if learner_session.current_node_id != current_step:
            raise ScenarioStepConflictError(
                "The submitted step does not match the current session step."
            )
    elif current_step != scenario.start_node_id:
        raise ScenarioStepConflictError(
            "A new session must start at the scenario's initial step."
        )

    # Evaluate the choice with the existing scenario engine.
    try:
        outcome = submit_scenario_choice(
            _scenario_definition(scenario),
            current_step,
            choice_id,
        )
    except ScenarioChoiceNotFoundError as exc:
        raise ScenarioChoiceInvalidError(
            f"Choice '{choice_id}' is not available at step '{current_step}'."
        ) from exc

    next_node = outcome["next_node"]
    completed = outcome["completed"]

    try:
        # Create a session when the learner submits their first choice.
        if learner_session is None:
            learner_session = ScenarioSession(
                user_id=user_id,
                scenario_id=scenario_id,
                current_node_id=current_step,
                simulation_type="general",
                is_completed=False,
            )

            db.add(learner_session)
            db.flush()

        # Save the learner's answer and the resulting feedback.
        saved_response = ScenarioResponse(
            session_id=learner_session.id,
            node_id=current_step,
            choice_id=choice_id,
            next_node_id=(
                next_node["node_id"]
                if next_node is not None
                else None
            ),
            feedback=outcome["feedback"],
        )

        db.add(saved_response)

        # Advance the session or mark it as completed.
        if completed:
            learner_session.is_completed = True
            learner_session.completed_at = datetime.now(timezone.utc)
        else:
            learner_session.current_node_id = next_node["node_id"]

        db.commit()

    except Exception:
        db.rollback()
        raise

    # Return the agreed frontend response format.
    if completed:
        return ScenarioRespondResponse(
            scenario_id=scenario_id,
            feedback=outcome["feedback"],
            current_step=None,
            prompt=None,
            choices=[],
            completed=True,
        )

    next_step = _public_step(
        scenario,
        next_node["node_id"],
    )

    return ScenarioRespondResponse(
        scenario_id=scenario_id,
        feedback=outcome["feedback"],
        current_step=next_step.current_step,
        prompt=next_step.prompt,
        choices=next_step.choices,
        completed=False,
    )