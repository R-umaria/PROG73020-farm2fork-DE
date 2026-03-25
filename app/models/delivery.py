from dataclasses import dataclass

@dataclass
class Delivery:
    id: int
    order_id: str
    customer_name: str
    address: str
    status: str
    latitude: float
    longitude: float
