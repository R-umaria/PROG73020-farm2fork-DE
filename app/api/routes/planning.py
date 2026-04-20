from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.planning import GroupBacklogResponse, PlanningResponse, ScheduleRoutesResponse
from app.schemas.routing import RouteMapResponse
from app.services.planning_service import PlanningService

router = APIRouter()


@router.post("/geocode-pending", response_model=PlanningResponse)
def geocode_pending_requests(db: Session = Depends(get_db)):
    service = PlanningService(db)
    try:
        return service.geocode_pending_requests()
    finally:
        service.close()


@router.post(
    "/group-backlog",
    response_model=GroupBacklogResponse,
    summary="Group plannable backlog deterministically (v1)",
    response_description="Deterministic planning groups for eligible delivery requests, keyed by handling type and derived region (v1).",
)
def group_backlog(db: Session = Depends(get_db)):
    service = PlanningService(db)
    try:
        return service.group_backlog()
    finally:
        service.close()


@router.post(
    "/schedule",
    response_model=ScheduleRoutesResponse,
    summary="Schedule deterministic route groups and apply default driver assignment (v1)",
    response_description="Creates route groups and route stops from eligible grouped backlog, then applies the default deterministic driver assignment heuristic (v1).",
)
def schedule_routes(db: Session = Depends(get_db)):
    service = PlanningService(db)
    try:
        return service.schedule_routes()
    finally:
        service.close()


@router.post(
    "/route-group/{route_group_id}/optimize",
    response_model=PlanningResponse,
    summary="Optimize route for a single route group via Valhalla",
)
def optimize_route_group(route_group_id: UUID, db: Session = Depends(get_db)):
    service = PlanningService(db)
    try:
        success = service.optimize_route_group(route_group_id)
        return PlanningResponse(message="Route optimized" if success else "Routing skipped or unavailable")
    finally:
        service.close()


@router.get(
    "/route-group/{route_group_id}/map",
    response_model=RouteMapResponse,
    summary="Get route geometry and stop coordinates for a route group",
)
def get_route_group_map(route_group_id: UUID, db: Session = Depends(get_db)):
    service = PlanningService(db)
    try:
        return service.get_route_map(route_group_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        service.close()
