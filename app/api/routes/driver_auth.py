from fastapi import APIRouter, HTTPException
from app.schemas.auth import DriverTokenSessionRequest, DriverTokenSessionResponse
from app.services.driver_auth_service import DriverAccountNotFoundError, DriverAuthService
from app.utils.jwt_tokens import DriverTokenError

router = APIRouter()
service = DriverAuthService()

@router.post('/session', response_model=DriverTokenSessionResponse)
def create_driver_session(payload: DriverTokenSessionRequest):
    try:
        return service.create_session_from_token(payload.token)
    except DriverTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DriverAccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
