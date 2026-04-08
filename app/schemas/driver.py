from pydantic import BaseModel

# MOCK IMPLEMENTATION - In a real application, this would be replaced with actual database models and logic
class DriverResponse(BaseModel):
    id: int
    name: str
    vehicle_type: str
    status: str


class DriverScheduleResponse(BaseModel):
    driver_id: int
    stops: list[dict]