from collections.abc import Mapping
from typing import Any


class ScenarioError(ValueError):
    """Base exception for scenario-engine errors."""


class ScenarioDefinitionError(ScenarioError):
    """Raised when a scenario definition is invalid."""


class ScenarioNodeNotFoundError(ScenarioError):
    """Raised when a requested scenario step does not exist."""


class ScenarioChoiceNotFoundError(ScenarioError):
    """Raised when a choice does not exist at the current step."""


def validate_scenario(scenario: Mapping[str, Any]) -> None:
    """Validate a scenario definition and all its branching targets."""
    if not isinstance(scenario, Mapping):
        raise ScenarioDefinitionError("Scenario must be an object.")

    for field in ("id", "title", "start_node_id"):
        value = scenario.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ScenarioDefinitionError(
                f"Scenario field '{field}' must be a non-empty string."
            )

    nodes = scenario.get("nodes")
    if not isinstance(nodes, Mapping) or not nodes:
        raise ScenarioDefinitionError(
            "Scenario must contain a non-empty 'nodes' object."
        )

    if scenario["start_node_id"] not in nodes:
        raise ScenarioDefinitionError(
            "The start_node_id must reference an existing node."
        )

    for node_id, node in nodes.items():
        if not isinstance(node_id, str) or not node_id.strip():
            raise ScenarioDefinitionError("Node IDs must be non-empty strings.")

        if not isinstance(node, Mapping):
            raise ScenarioDefinitionError(
                f"Node '{node_id}' must be an object."
            )

        prompt = node.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ScenarioDefinitionError(
                f"Node '{node_id}' needs a non-empty prompt."
            )

        choices = node.get("choices")
        if not isinstance(choices, list):
            raise ScenarioDefinitionError(
                f"Node '{node_id}' must have a choices list."
            )

        seen_choice_ids: set[str] = set()

        for choice in choices:
            if not isinstance(choice, Mapping):
                raise ScenarioDefinitionError(
                    f"Every choice in node '{node_id}' must be an object."
                )

            choice_id = choice.get("id")
            label = choice.get("label")

            if not isinstance(choice_id, str) or not choice_id.strip():
                raise ScenarioDefinitionError(
                    f"Every choice in node '{node_id}' needs an ID."
                )

            if choice_id in seen_choice_ids:
                raise ScenarioDefinitionError(
                    f"Duplicate choice ID '{choice_id}' in node '{node_id}'."
                )
            seen_choice_ids.add(choice_id)

            if not isinstance(label, str) or not label.strip():
                raise ScenarioDefinitionError(
                    f"Choice '{choice_id}' needs a non-empty label."
                )

            if "next_node_id" not in choice:
                raise ScenarioDefinitionError(
                    f"Choice '{choice_id}' needs next_node_id; "
                    "use null to finish the scenario."
                )

            next_node_id = choice["next_node_id"]
            if next_node_id is not None and (
                not isinstance(next_node_id, str)
                or next_node_id not in nodes
            ):
                raise ScenarioDefinitionError(
                    f"Choice '{choice_id}' references an unknown next node."
                )

            feedback = choice.get("feedback")
            if feedback is not None and not isinstance(feedback, str):
                raise ScenarioDefinitionError(
                    f"Feedback for choice '{choice_id}' must be text."
                )


def get_scenario_step(
    scenario: Mapping[str, Any],
    node_id: str | None = None,
) -> dict[str, Any]:
    """Return a public view of a scenario step without revealing its answer."""
    validate_scenario(scenario)

    resolved_node_id = node_id or scenario["start_node_id"]
    node = scenario["nodes"].get(resolved_node_id)

    if node is None:
        raise ScenarioNodeNotFoundError(
            f"Node '{resolved_node_id}' does not exist."
        )

    return {
        "scenario_id": scenario["id"],
        "node_id": resolved_node_id,
        "prompt": node["prompt"],
        "choices": [
            {"id": choice["id"], "label": choice["label"]}
            for choice in node["choices"]
        ],
    }


def submit_scenario_choice(
    scenario: Mapping[str, Any],
    node_id: str,
    choice_id: str,
) -> dict[str, Any]:
    """Evaluate a choice and return feedback and the next scenario step."""
    current_step = get_scenario_step(scenario, node_id)
    current_node = scenario["nodes"][current_step["node_id"]]

    selected_choice = next(
        (
            choice
            for choice in current_node["choices"]
            if choice["id"] == choice_id
        ),
        None,
    )

    if selected_choice is None:
        raise ScenarioChoiceNotFoundError(
            f"Choice '{choice_id}' does not exist at node '{node_id}'."
        )

    next_node_id = selected_choice["next_node_id"]
    completed = next_node_id is None

    next_step = (
        None
        if completed
        else get_scenario_step(scenario, next_node_id)
    )

    return {
        "scenario_id": scenario["id"],
        "node_id": current_step["node_id"],
        "choice_id": choice_id,
        "feedback": selected_choice.get("feedback"),
        "next_node": next_step,
        "completed": completed,
    }
