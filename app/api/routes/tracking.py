from fastapi import APIRouter

from app.schemas.tracking import DeliveryStatusResponse
from app.services.tracking_service import TrackingService

router = APIRouter()
service = TrackingService()


@router.get(
    "/{order_id}",
    response_model=DeliveryStatusResponse,
    response_model_exclude_none=True,
    summary="Get delivery execution status (v1)",
    response_description="Delivery execution status for an order as exposed by the tracking contract (v1).",
)
def get_delivery_status(order_id: int):
    return service.get_status(order_id)
