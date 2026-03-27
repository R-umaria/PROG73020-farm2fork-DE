from pydantic import BaseModel

class DriverScheduleResponse(BaseModel):
    driver_id: int
    stops: list[dict]
