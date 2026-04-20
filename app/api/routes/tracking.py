"""Tracking API exposing the persisted delivery execution read model."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tracking import DeliveryStatusResponse
from app.services.tracking_service import TrackingService

router = APIRouter()


@router.get(
    "/{order_id}",
    response_model=DeliveryStatusResponse,
    response_model_exclude_none=True,
    summary="Get delivery execution status (v1)",
    response_description="DB-backed delivery execution status and timeline for an order (v1).",
)
def get_delivery_status(order_id: int, db: Session = Depends(get_db)):
    """Return the persisted status/timeline view for a tracked order."""

    service = TrackingService(db)
    try:
        result = service.get_status(order_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Tracked delivery status not found for order_id {order_id}")
        return result
    finally:
        service.close()
