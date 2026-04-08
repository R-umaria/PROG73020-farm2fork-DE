from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DriverSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, title="DriverSummaryResponseV1")

    driver_id: int
    driver_name: str
    vehicle_type: str
    driver_status: str


class DriverScheduleStopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, title="DriverScheduleStopResponseV1")

    route_stop_id: UUID
    route_group_id: UUID
    delivery_request_id: UUID
    order_id: int
    sequence: int
    stop_status: str
    estimated_arrival: datetime | None = None
    address: str | None = None


class DriverScheduleResponse(BaseModel):
    model_config = ConfigDict(title="DriverScheduleResponseV1")

    driver_id: int
    driver_name: str
    vehicle_type: str
    driver_status: str
    stops: list[DriverScheduleStopResponse]


class DriverDayActionResponse(BaseModel):
    model_config = ConfigDict(title="DriverDayActionResponseV1")

    driver_id: int
    driver_name: str
    driver_status: str
    message: str


class RouteStopActionResponse(BaseModel):
    model_config = ConfigDict(title="RouteStopActionResponseV1")

    route_stop_id: UUID
    stop_status: str
    message: str


DriverResponse = DriverSummaryResponse
