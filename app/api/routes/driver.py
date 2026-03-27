from fastapi import APIRouter
from app.services.driver_service import DriverService

router = APIRouter()
service = DriverService()

@router.get("/schedule/today/{driver_id}")
def get_todays_schedule(driver_id: int):
    return service.get_todays_schedule(driver_id)

@router.post("/start-day/{driver_id}")
def start_day(driver_id: int):
    return service.start_day(driver_id)

@router.post("/stops/{route_stop_id}/complete")
def complete_stop(route_stop_id: int):
    return service.complete_stop(route_stop_id)
