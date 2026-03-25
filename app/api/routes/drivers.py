from fastapi import APIRouter
from app.schemas.driver import DriverResponse
from app.services.driver_service import DriverService

router = APIRouter()
service = DriverService()

@router.get("/", response_model=list[DriverResponse])
def list_drivers():
    return service.list_drivers()
