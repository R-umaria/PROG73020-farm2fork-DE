from fastapi import APIRouter

from app.schemas.tracking import DeliveryStatusResponse
from app.services.tracking_service import TrackingService

router = APIRouter()
service = TrackingService()


@router.get("/{order_id}", response_model=DeliveryStatusResponse)
def get_delivery_status(order_id: str):
    return service.get_status(order_id)
