from pydantic import BaseModel

class AssignmentResponse(BaseModel):
    id: int
    delivery_id: int
    driver_id: int
    status: str
