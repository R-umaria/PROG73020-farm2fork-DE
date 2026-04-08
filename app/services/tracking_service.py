from app.core.delivery_status import INITIAL_DELIVERY_EXECUTION_STATUS
from app.schemas.tracking import DeliveryStatusResponse


class TrackingService:
    def get_status(self, order_id: str) -> DeliveryStatusResponse:
        return DeliveryStatusResponse(
            order_id=order_id,
            delivery_status=INITIAL_DELIVERY_EXECUTION_STATUS,
        )
