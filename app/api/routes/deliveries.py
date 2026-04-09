from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.delivery import DeliveryCreate, DeliveryResponse
from app.services.delivery_service import DeliveryService

router = APIRouter()
service = DeliveryService()


@router.get(
    "/",
    response_model=list[DeliveryResponse],
    response_model_exclude_none=True,
    summary="List delivery request records (v1)",
    response_description="Delivery request records exposed by the delivery execution service (v1).",
)
def list_deliveries():
    return service.list_deliveries()


@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
    response_model_exclude_none=True,
    summary="Get delivery request record (v1)",
    response_description="A single delivery request record from the delivery execution service (v1).",
)
def get_delivery(delivery_id: UUID):
    delivery = service.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.post(
    "/",
    response_model=DeliveryResponse,
    response_model_exclude_none=True,
    status_code=201,
    summary="Create delivery request record manually (v1)",
    response_description="Non-primary manual creation path for a delivery request record (v1). Prefer POST /api/delivery-requests/ for the intake contract.",
)
def create_delivery(payload: DeliveryCreate):
    return service.create_delivery(payload)
