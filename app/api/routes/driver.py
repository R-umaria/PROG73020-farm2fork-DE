from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)
from app.schemas.driver import (
    DriverDayActionResponse,
    DriverScheduleResponse,
    DriverSummaryResponse,
    RouteStopActionResponse,
)
from app.services.driver_service import DriverService, RouteStopNotFoundError

router = APIRouter()
service = DriverService()


@router.get(
    "/schedule/today/{driver_id}",
    response_model=DriverScheduleResponse,
    responses={
        404: {"description": "The driver could not be found in the upstream Driver Service (v1)."},
        502: {"description": "Driver Service returned an invalid or unusable response (v1)."},
        504: {"description": "Driver Service timed out while resolving driver data (v1)."},
    },
    summary="Get the current driver's assigned route stops (v1)",
    response_description="Driver schedule view combining upstream driver roster data with locally planned route stops (v1).",
)
def get_todays_schedule(driver_id: int):
    try:
        return service.get_todays_schedule(driver_id)
    except UpstreamNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except UpstreamBadResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/start-day/{driver_id}",
    response_model=DriverDayActionResponse,
    responses={
        404: {"description": "The driver could not be found in the upstream Driver Service (v1)."},
        502: {"description": "Driver Service returned an invalid or unusable response (v1)."},
        504: {"description": "Driver Service timed out while resolving driver data (v1)."},
    },
    summary="Acknowledge driver day start (v1)",
    response_description="A lightweight driver-day acknowledgement using the explicit v1 driver contract.",
)
def start_day(driver_id: int):
    try:
        return service.start_day(driver_id)
    except UpstreamNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except UpstreamBadResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/stops/{route_stop_id}/complete",
    response_model=RouteStopActionResponse,
    responses={404: {"description": "The route stop was not found (v1)."}},
    summary="Mark a route stop completed (v1)",
    response_description="Updates the local route-stop read model using the explicit v1 stop contract.",
)
def complete_stop(route_stop_id: UUID):
    try:
        return service.complete_stop(route_stop_id)
    except RouteStopNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=list[DriverSummaryResponse],
    responses={
        404: {"description": "The upstream driver roster endpoint or requested driver was not found (v1)."},
        502: {"description": "Driver Service returned an invalid or unusable response (v1)."},
        504: {"description": "Driver Service timed out while resolving driver data (v1)."},
    },
    summary="Compatibility alias for the v1 driver roster contract",
    response_description="Compatibility alias for `/api/drivers/`; consumers should prefer the plural collection route moving forward.",
)
def list_drivers_alias():
    try:
        return service.list_drivers()
    except UpstreamNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except UpstreamBadResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
