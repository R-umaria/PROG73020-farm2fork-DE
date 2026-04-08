from fastapi import APIRouter

from app.schemas.planning import GroupBacklogResponse, PlanningResponse
from app.services.planning_service import PlanningService

router = APIRouter()
service = PlanningService()


@router.post("/geocode-pending", response_model=PlanningResponse)
def geocode_pending_requests():
    return service.geocode_pending_requests()


@router.post(
    "/group-backlog",
    response_model=GroupBacklogResponse,
    summary="Group plannable backlog deterministically (v1)",
    response_description="Deterministic planning groups for eligible delivery requests, keyed by handling type and derived region (v1).",
)
def group_backlog():
    return service.group_backlog()


@router.post("/schedule", response_model=PlanningResponse)
def schedule_routes():
    return service.schedule_routes()
