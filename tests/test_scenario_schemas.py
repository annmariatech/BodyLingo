import pytest
from pydantic import ValidationError

from backend.schemas.scenario import (
    ScenarioRespondRequest,
    ScenarioRespondResponse,
)


def test_valid_scenario_request():
    request = ScenarioRespondRequest(
        node_id="start",
        choice_id="ask-gently",
    )

    assert request.node_id == "start"
    assert request.choice_id == "ask-gently"


def test_request_rejects_blank_node_id():
    with pytest.raises(ValidationError):
        ScenarioRespondRequest(
            node_id="   ",
            choice_id="ask-gently",
        )


def test_request_rejects_missing_choice_id():
    with pytest.raises(ValidationError):
        ScenarioRespondRequest(node_id="start")


def test_request_rejects_extra_user_id():
    with pytest.raises(ValidationError):
        ScenarioRespondRequest(
            node_id="start",
            choice_id="ask-gently",
            user_id="someone-else",
        )


def test_response_supports_next_step():
    response = ScenarioRespondResponse(
        scenario_id="team-communication",
        node_id="start",
        choice_id="ask-gently",
        feedback="A gentle question invites conversation.",
        next_node={
            "scenario_id": "team-communication",
            "node_id": "support",
            "prompt": "What do you say next?",
            "choices": [
                {"id": "offer-space", "label": "Offer to talk later"}
            ],
        },
        completed=False,
    )

    assert response.next_node.node_id == "support"
    assert response.completed is False


def test_response_supports_completion():
    response = ScenarioRespondResponse(
        scenario_id="team-communication",
        node_id="support",
        choice_id="offer-space",
        feedback="Respecting their choice gives them space.",
        next_node=None,
        completed=True,
    )

    assert response.next_node is None
    assert response.completed is True