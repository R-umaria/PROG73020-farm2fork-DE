from pydantic import BaseModel

from app.core.delivery_status import DeliveryExecutionStatus


class DeliveryStatusResponse(BaseModel):
    order_id: str
    delivery_status: DeliveryExecutionStatus
