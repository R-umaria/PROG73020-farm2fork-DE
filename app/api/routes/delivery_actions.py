from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.delivery_status import InvalidStatusTransitionError
from app.services.delivery_actions_service import DeliveryActionsService

router = APIRouter()


class StartDeliveryRequest(BaseModel):
    pass


class CompleteDeliveryRequest(BaseModel):
    received_by: str
    proof_of_delivery_url: str | None = None


class FailDeliveryRequest(BaseModel):
    exception_type: str
    description: str
    retry_allowed: bool = False


@router.post("/deliveries/{delivery_execution_id}/start")
def start_delivery(delivery_execution_id: UUID, db: Session = Depends(get_db)):
    service = DeliveryActionsService(db)
    try:
        result = service.start_delivery(delivery_execution_id)
        if not result:
            raise HTTPException(status_code=404, detail="Delivery execution not found")
        return {"status": result.current_status, "id": str(result.id)}
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        service.close()


@router.post("/deliveries/{delivery_execution_id}/complete")
def complete_delivery(delivery_execution_id: UUID, payload: CompleteDeliveryRequest, db: Session = Depends(get_db)):
    service = DeliveryActionsService(db)
    try:
        result = service.complete_delivery(
            delivery_execution_id=delivery_execution_id,
            received_by=payload.received_by,
            proof_url=payload.proof_of_delivery_url,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Delivery execution not found")
        return {"confirmed": True, "received_by": result.received_by}
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        service.close()


@router.post("/deliveries/{delivery_execution_id}/fail")
def fail_delivery(delivery_execution_id: UUID, payload: FailDeliveryRequest, db: Session = Depends(get_db)):
    service = DeliveryActionsService(db)
    try:
        result = service.fail_delivery(
            delivery_execution_id=delivery_execution_id,
            exception_type=payload.exception_type,
            description=payload.description,
            retry_allowed=payload.retry_allowed,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Delivery execution not found")
        return {"exception_type": result.exception_type, "retry_allowed": result.retry_allowed}
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        service.close()
