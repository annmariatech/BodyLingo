import pytest

from backend.services.scenario_engine import (
    ScenarioChoiceNotFoundError,
    ScenarioDefinitionError,
    ScenarioNodeNotFoundError,
    get_scenario_step,
    submit_scenario_choice,
)


@pytest.fixture
def sample_scenario():
    return {
        "id": "team-communication",
        "title": "Responding to a quiet teammate",
        "start_node_id": "start",
        "nodes": {
            "start": {
                "prompt": "Your teammate has become quiet. What do you do?",
                "choices": [
                    {
                        "id": "ask-gently",
                        "label": "Ask if they are okay",
                        "next_node_id": "support",
                        "feedback": "A gentle question invites conversation.",
                    },
                    {
                        "id": "assume",
                        "label": "Assume they are upset with you",
                        "next_node_id": "reflect",
                        "feedback": "Silence alone does not reveal someone's feelings.",
                    },
                ],
            },
            "support": {
                "prompt": "Your teammate says they are tired. What next?",
                "choices": [
                    {
                        "id": "offer-space",
                        "label": "Offer to talk later",
                        "next_node_id": None,
                        "feedback": "Respecting their choice gives them space.",
                    },
                ],
            },
            "reflect": {
                "prompt": "What else could explain their silence?",
                "choices": [
                    {
                        "id": "consider-context",
                        "label": "Consider other explanations",
                        "next_node_id": "support",
                        "feedback": "Context matters when interpreting cues.",
                    },
                ],
            },
        },
    }


def test_get_start_step(sample_scenario):
    step = get_scenario_step(sample_scenario)

    assert step["node_id"] == "start"
    assert len(step["choices"]) == 2
    assert "feedback" not in step["choices"][0]
    assert "next_node_id" not in step["choices"][0]


def test_choice_follows_correct_branch(sample_scenario):
    result = submit_scenario_choice(
        sample_scenario, "start", "ask-gently"
    )

    assert result["next_node"]["node_id"] == "support"
    assert result["completed"] is False
    assert "gentle question" in result["feedback"]


def test_different_choice_follows_different_branch(sample_scenario):
    result = submit_scenario_choice(
        sample_scenario, "start", "assume"
    )

    assert result["next_node"]["node_id"] == "reflect"
    assert result["completed"] is False


def test_final_choice_completes_scenario(sample_scenario):
    result = submit_scenario_choice(
        sample_scenario, "support", "offer-space"
    )

    assert result["completed"] is True
    assert result["next_node"] is None


def test_invalid_choice_is_rejected(sample_scenario):
    with pytest.raises(ScenarioChoiceNotFoundError):
        submit_scenario_choice(
            sample_scenario, "start", "unknown-choice"
        )


def test_invalid_node_is_rejected(sample_scenario):
    with pytest.raises(ScenarioNodeNotFoundError):
        get_scenario_step(sample_scenario, "unknown-node")


def test_invalid_branch_target_is_rejected(sample_scenario):
    sample_scenario["nodes"]["start"]["choices"][0][
        "next_node_id"
    ] = "missing-node"

    with pytest.raises(ScenarioDefinitionError):
        get_scenario_step(sample_scenario)