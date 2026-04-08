from uuid import UUID

from fastapi import APIRouter

from app.schemas.intake import (
    CustomerSyncResponse,
    DeliveryRequestCreate,
    IntakeResponse,
)
from app.services.intake_service import IntakeService

router = APIRouter()
service = IntakeService()


@router.post(
    "/",
    response_model=IntakeResponse,
    response_model_exclude_none=True,
    status_code=201,
    summary="Accept delivery request intake (v1)",
    response_description="Delivery request accepted by the intake contract (v1).",
)
def create_delivery_request(payload: DeliveryRequestCreate):
    return service.receive_delivery_request(payload)


@router.post(
    "/{delivery_request_id}/customer-sync",
    response_model=CustomerSyncResponse,
    summary="Trigger customer sync placeholder (v1)",
    response_description="Placeholder response for customer data sync linked to a delivery request (v1).",
)
def sync_customer_details(delivery_request_id: UUID):
    return service.sync_customer_details(delivery_request_id)
