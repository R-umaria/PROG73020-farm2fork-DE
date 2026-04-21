from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)
from app.schemas.driver import DriverSummaryResponse
from app.services.driver_service import DriverService

router = APIRouter()


@router.get(
    "/",
    response_model=list[DriverSummaryResponse],
    responses={
        404: {"description": "The upstream driver roster endpoint or requested driver was not found (v1)."},
        502: {"description": "Driver Service returned an invalid or unusable response (v1)."},
        504: {"description": "Driver Service timed out while resolving driver data (v1)."},
    },
    summary="List available driver roster data (v1)",
    response_description="Driver roster projected from the Driver Service dependency using the explicit v1 driver contract.",
)
def list_drivers(db: Session = Depends(get_db)):
    service = DriverService(db)
    try:
        return service.list_drivers()
    except UpstreamNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except UpstreamBadResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        service.close()
