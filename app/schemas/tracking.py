from pydantic import BaseModel

class DeliveryStatusResponse(BaseModel):
    order_id: str
    delivery_status: str
