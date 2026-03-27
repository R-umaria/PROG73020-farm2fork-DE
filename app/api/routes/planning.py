from fastapi import APIRouter
from app.services.planning_service import PlanningService

router = APIRouter()
service = PlanningService()

@router.post("/geocode-pending")
def geocode_pending_requests():
    return service.geocode_pending_requests()

@router.post("/group-backlog")
def group_backlog():
    return service.group_backlog()

@router.post("/schedule")
def schedule_routes():
    return service.schedule_routes()
