from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...guardian_dossier import build_dossier
from ...policy_engine import PolicyEngine, PolicyEngineError
from ...schemas import TeamSimulationRequest

router = APIRouter(prefix="/team", tags=["team"])

_engine = PolicyEngine()


@router.post("/simulate")
async def simulate_team(payload: TeamSimulationRequest):
    if not payload.team_ids:
        raise HTTPException(status_code=400, detail="team_ids cannot be empty")

    dossier = build_dossier(
        payload.team_ids,
        mission_profile=payload.mission_profile,
        evidence_limit=payload.evidence_limit,
    )

    overrides = payload.overrides.dict(exclude_none=True) if payload.overrides else None

    try:
        evaluation = _engine.evaluate(dossier, overrides=overrides)
    except PolicyEngineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"dossier": dossier, "evaluation": evaluation}
