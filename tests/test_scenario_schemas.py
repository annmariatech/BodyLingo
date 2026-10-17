import pytest
from pydantic import ValidationError

from backend.schemas.scenario import (
    ScenarioRespondRequest,
    ScenarioRespondResponse,
    ScenarioStepResponse,
)


def test_valid_scenario_request():
    request = ScenarioRespondRequest(
        current_step="step_1",
        choice_id="ask_gently",
    )

    assert request.current_step == "step_1"
    assert request.choice_id == "ask_gently"


def test_request_rejects_blank_current_step():
    with pytest.raises(ValidationError):
        ScenarioRespondRequest(
            current_step="   ",
            choice_id="ask_gently",
        )


def test_request_rejects_missing_choice_id():
    with pytest.raises(ValidationError):
        ScenarioRespondRequest(current_step="step_1")


def test_request_rejects_extra_user_id():
    with pytest.raises(ValidationError):
        ScenarioRespondRequest(
            current_step="step_1",
            choice_id="ask_gently",
            user_id="someone-else",
        )


def test_step_uses_frontend_choice_format():
    step = ScenarioStepResponse(
        scenario_id="team_meeting_01",
        current_step="step_1",
        prompt="Your teammate becomes quiet. What do you do?",
        choices=[
            {
                "id": "a",
                "text": "Ask privately if they need a break",
            }
        ],
    )

    assert step.current_step == "step_1"
    assert step.choices[0].text == (
        "Ask privately if they need a break"
    )


def test_response_supports_next_step():
    response = ScenarioRespondResponse(
        scenario_id="team_meeting_01",
        feedback="A gentle question invites conversation.",
        current_step="step_2",
        prompt="What would you say next?",
        choices=[
            {"id": "b", "text": "Offer to talk later"}
        ],
        completed=False,
    )

    assert response.current_step == "step_2"
    assert response.choices[0].id == "b"
    assert response.completed is False


def test_response_supports_completion():
    response = ScenarioRespondResponse(
        scenario_id="team_meeting_01",
        feedback="You respected their choice.",
        current_step=None,
        prompt=None,
        choices=[],
        completed=True,
    )

    assert response.current_step is None
    assert response.choices == []
    assert response.completed is True