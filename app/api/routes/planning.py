from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.planning import GroupBacklogResponse, PlanningResponse, ScheduleRoutesResponse
from app.schemas.routing import RouteMapResponse
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


@router.post(
    "/schedule",
    response_model=ScheduleRoutesResponse,
    summary="Schedule deterministic route groups and apply default driver assignment (v1)",
    response_description="Creates route groups and route stops from eligible grouped backlog, then applies the default deterministic driver assignment heuristic (v1).",
)
def schedule_routes():
    return service.schedule_routes()


@router.post(
    "/route-group/{route_group_id}/optimize",
    response_model=PlanningResponse,
    summary="Optimize route for a single route group via Valhalla",
)
def optimize_route_group(route_group_id: UUID):
    success = service.optimize_route_group(route_group_id)
    return PlanningResponse(
        message="Route optimized" if success else "Routing skipped or unavailable"
    )


@router.get(
    "/route-group/{route_group_id}/map",
    response_model=RouteMapResponse,
    summary="Get route geometry and stop coordinates for a route group",
)
def get_route_group_map(route_group_id: UUID):
    try:
        return service.get_route_map(route_group_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
