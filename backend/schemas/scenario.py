from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, Field


ScenarioID = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class ScenarioChoiceResponse(BaseModel):
    """A choice visible to the learner."""

    id: ScenarioID
    text: str


class ScenarioStepResponse(BaseModel):
    """The current scenario step shown to the learner."""

    scenario_id: ScenarioID
    current_step: ScenarioID
    prompt: str
    choices: list[ScenarioChoiceResponse]


class ScenarioSummaryResponse(BaseModel):
    """Basic information shown in a scenario listing."""

    id: ScenarioID
    title: str
    description: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    media_placeholder: str = "Text-based practice; no media asset is included."


class ScenarioListResponse(BaseModel):
    """Response containing the available scenarios."""

    scenarios: list[ScenarioSummaryResponse]


class ScenarioDetailResponse(ScenarioStepResponse):
    """Scenario details and its initial step."""

    title: str = ""
    description: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    media_placeholder: str = "Text-based practice; no media asset is included."


class ScenarioRespondRequest(BaseModel):
    """The learner's choice at the current scenario step."""

    model_config = ConfigDict(extra="forbid")

    current_step: ScenarioID
    choice_id: ScenarioID


class ScenarioRespondResponse(BaseModel):
    """Feedback and the next step after a learner submits a choice."""

    scenario_id: ScenarioID
    feedback: str | None = None
    current_step: ScenarioID | None = None
    prompt: str | None = None
    choices: list[ScenarioChoiceResponse] = Field(default_factory=list)
    completed: bool


class ScenarioProgressItem(BaseModel):
    scenario_id: ScenarioID
    title: str
    is_completed: bool
    started_at: datetime
    completed_at: datetime | None = None
    response_count: int


class ScenarioProgressResponse(BaseModel):
    completed_scenarios: list[str]
    sessions: list[ScenarioProgressItem]
