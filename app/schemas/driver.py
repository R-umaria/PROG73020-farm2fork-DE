from pydantic import BaseModel

class DriverResponse(BaseModel):
    id: int
    name: str
    vehicle_type: str
    status: str
