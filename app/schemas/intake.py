from pydantic import BaseModel

class DeliveryRequestCreate(BaseModel):
    order_id: str
    customer_id: str
    order_timestamp: str
    order_type: str
    list_of_items_ordered: list[dict]

class IntakeResponse(BaseModel):
    message: str
    order_id: str
