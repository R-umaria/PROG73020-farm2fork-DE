from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.repositories.driver_portal_repository import ShiftUnavailableError
from app.schemas.shift import AvailableShiftResponse, StartShiftRequest, StartShiftResponse
from app.services.shift_service import ShiftService

router = APIRouter()
service = ShiftService()

@router.get('/available', response_model=list[AvailableShiftResponse])
def list_available_shifts():
    return service.list_available_shifts()

@router.post('/{route_group_id}/start', response_model=StartShiftResponse)
def start_shift(route_group_id: UUID, payload: StartShiftRequest):
    try:
        return service.start_shift(route_group_id=route_group_id, driver_id=payload.driver_id)
    except ShiftUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
