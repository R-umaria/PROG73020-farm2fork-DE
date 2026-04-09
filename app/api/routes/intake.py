from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.intake import (
    CustomerSyncResponse,
    DeliveryRequestCreate,
    IntakeResponse,
)
from app.services.intake_service import IntakeConflictError, IntakeService

router = APIRouter()
service = IntakeService()


@router.post(
    "/",
    response_model=IntakeResponse,
    response_model_exclude_none=True,
    status_code=201,
    responses={
        200: {"description": "Idempotent duplicate accepted and mapped to the existing delivery request record (v1)."},
        409: {"description": "A conflicting duplicate payload was submitted for an existing order_id (v1)."},
    },
    summary="Accept delivery request intake (v1)",
    response_description="Delivery request accepted by the intake contract (v1).",
)
def create_delivery_request(payload: DeliveryRequestCreate, response: Response):
    try:
        intake_response = service.receive_delivery_request(payload)
    except IntakeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    message = intake_response.message if hasattr(intake_response, "message") else intake_response.get("message")
    if message == "Delivery request already received (v1)":
        response.status_code = status.HTTP_200_OK

    return intake_response


@router.post(
    "/{delivery_request_id}/customer-sync",
    response_model=CustomerSyncResponse,
    summary="Trigger customer sync placeholder (v1)",
    response_description="Placeholder response for customer data sync linked to a delivery request (v1).",
)
def sync_customer_details(delivery_request_id: UUID):
    return service.sync_customer_details(delivery_request_id)
