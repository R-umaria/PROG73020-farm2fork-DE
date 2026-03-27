from fastapi import APIRouter
from app.services.tracking_service import TrackingService

router = APIRouter()
service = TrackingService()

@router.get("/{order_id}")
def get_delivery_status(order_id: str):
    return service.get_status(order_id)
