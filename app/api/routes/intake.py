from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)
from app.schemas.intake import (
    CustomerSyncResponse,
    DeliveryRequestCreate,
    IntakeResponse,
)
from app.services.intake_service import (
    DeliveryRequestNotFoundError,
    IntakeConflictError,
    IntakeService,
)

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
    responses={
        404: {"description": "The delivery request or upstream customer record was not found (v1)."},
        502: {"description": "An upstream dependency returned an invalid or unusable response (v1)."},
        504: {"description": "An upstream dependency timed out during customer sync (v1)."},
    },
    summary="Fetch customer details and geocode the address (v1)",
    response_description="Customer enrichment and geocode snapshot saved against the delivery request (v1).",
)
def sync_customer_details(delivery_request_id: UUID):
    try:
        return service.sync_customer_details(delivery_request_id)
    except DeliveryRequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except UpstreamBadResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
