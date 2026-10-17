"""Authenticated scenario library, branching responses and learner history."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import CurrentUser
from backend.models.scenario import Scenario
from backend.models.scenario_response import ScenarioResponse
from backend.models.scenario_session import ScenarioSession
from schemas.scenario import (
    ScenarioDetailResponse,
    ScenarioListResponse,
    ScenarioProgressItem,
    ScenarioProgressResponse,
    ScenarioRespondRequest,
    ScenarioRespondResponse,
)
from services.scenario_service import (
    ScenarioChoiceInvalidError,
    ScenarioNotFoundError,
    ScenarioStepConflictError,
    get_scenario_detail,
    list_scenarios,
    respond_to_scenario,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=ScenarioListResponse)
def get_scenarios(user: CurrentUser, db: Session = Depends(get_db)) -> ScenarioListResponse:
    del user  # Authenticated catalog access; learner identity is used for progress below.
    return list_scenarios(db)


@router.get("/progress", response_model=ScenarioProgressResponse)
def scenario_progress(user: CurrentUser, db: Session = Depends(get_db)) -> ScenarioProgressResponse:
    rows = db.scalars(
        select(ScenarioSession)
        .where(ScenarioSession.user_id == user.id)
        .order_by(ScenarioSession.started_at.desc())
    ).all()
    items = []
    for session in rows:
        scenario = db.get(Scenario, session.scenario_id)
        response_count = db.scalar(
            select(func.count()).select_from(ScenarioResponse).where(ScenarioResponse.session_id == session.id)
        ) or 0
        items.append(ScenarioProgressItem(
            scenario_id=session.scenario_id,
            title=scenario.title if scenario else session.scenario_id,
            is_completed=session.is_completed,
            started_at=session.started_at,
            completed_at=session.completed_at,
            response_count=response_count,
        ))
    return ScenarioProgressResponse(
        completed_scenarios=list(dict.fromkeys(item.scenario_id for item in items if item.is_completed)),
        sessions=items,
    )


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
def scenario_detail(scenario_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> ScenarioDetailResponse:
    try:
        return get_scenario_detail(db, scenario_id=scenario_id, user_id=user.id)
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{scenario_id}/respond", response_model=ScenarioRespondResponse)
def scenario_response(
    scenario_id: str,
    payload: ScenarioRespondRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> ScenarioRespondResponse:
    try:
        return respond_to_scenario(
            db,
            scenario_id=scenario_id,
            user_id=user.id,
            current_step=payload.current_step,
            choice_id=payload.choice_id,
        )
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ScenarioChoiceInvalidError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ScenarioStepConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
