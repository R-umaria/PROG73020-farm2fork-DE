from pydantic import BaseModel

#class DriverScheduleResponse(BaseModel):
   # driver_id: int
    #stops: list[dict]
class DriverResponse(BaseModel):
    id: int
    name: str
class DriverScheduleResponse(BaseModel):
    driver_id: int
    stops: list[dict]