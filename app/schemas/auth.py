from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DriverTokenSessionRequest(BaseModel):
    token: str = Field(min_length=1)


class DriverTokenSessionResponse(BaseModel):
    model_config = ConfigDict(title="DriverTokenSessionResponseV1")

    email: str
    user_type: str
    expires_at: datetime | None = None
    driver_id: int
    driver_name: str
    vehicle_type: str
    driver_status: str
    active_route_group_id: str | None = None
    active_route_group_name: str | None = None
    active_zone_code: str | None = None


class DriverJwtPayload(BaseModel):
    email: str
    user_type: str
    exp: int | None = None
    subject_id: int | None = None
    name: str | None = None
