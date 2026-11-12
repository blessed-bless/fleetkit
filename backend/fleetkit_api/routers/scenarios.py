from __future__ import annotations

from fastapi import APIRouter, HTTPException

from fleetkit_api.seed_scenarios import get_scenario, list_scenarios, scenario_summary

router = APIRouter(tags=["scenarios"])


@router.get("/scenarios")
async def scenarios() -> list[dict[str, str]]:
    return scenario_summary()


@router.get("/scenarios/{name}")
async def scenario_detail(name: str) -> dict:
    try:
        return get_scenario(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Сценарий не найден") from exc


@router.get("/scenarios-index")
async def scenarios_index() -> dict[str, list[str]]:
    return {"names": list_scenarios()}
