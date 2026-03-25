from pydantic import BaseModel

class DeliveryCreate(BaseModel):
    order_id: str
    customer_name: str
    address: str
    latitude: float
    longitude: float

class DeliveryResponse(BaseModel):
    id: int
    order_id: str
    customer_name: str
    address: str
    status: str
    latitude: float
    longitude: float
