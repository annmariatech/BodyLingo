from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


ScenarioID = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class ScenarioChoiceResponse(BaseModel):
    """A choice visible to the learner."""

    id: ScenarioID
    label: str


class ScenarioStepResponse(BaseModel):
    """A scenario step shown to the learner."""

    scenario_id: ScenarioID
    node_id: ScenarioID
    prompt: str
    choices: list[ScenarioChoiceResponse]


class ScenarioSummaryResponse(BaseModel):
    """Basic information for the scenario listing."""

    id: ScenarioID
    title: str
    description: str | None = None


class ScenarioListResponse(BaseModel):
    """Response containing the available scenarios."""

    scenarios: list[ScenarioSummaryResponse]


class ScenarioDetailResponse(ScenarioSummaryResponse):
    """Scenario details with the initial step."""

    start_step: ScenarioStepResponse


class ScenarioRespondRequest(BaseModel):
    """The learner's choice at the current scenario step."""

    model_config = ConfigDict(extra="forbid")

    node_id: ScenarioID
    choice_id: ScenarioID


class ScenarioRespondResponse(BaseModel):
    """Feedback and progression after a learner submits a choice."""

    scenario_id: ScenarioID
    node_id: ScenarioID
    choice_id: ScenarioID
    feedback: str | None = None
    next_node: ScenarioStepResponse | None
    completed: bool