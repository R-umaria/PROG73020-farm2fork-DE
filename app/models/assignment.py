from dataclasses import dataclass

@dataclass
class Assignment:
    id: int
    delivery_id: int
    driver_id: int
    status: str
