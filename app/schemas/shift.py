from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AvailableShiftResponse(BaseModel):
    model_config = ConfigDict(title="AvailableShiftResponseV1")

    route_group_id: UUID
    shift_name: str
    zone_code: str
    route_group_status: str
    total_stops: int
    estimated_distance_km: float | None = None
    estimated_duration_min: int | None = None
    scheduled_date: datetime
    first_eta: datetime | None = None
    last_eta: datetime | None = None
    warehouse_name: str
    warehouse_address: str
    stop_preview: list[str] = []


class StartShiftRequest(BaseModel):
    driver_id: int


class StartShiftResponse(BaseModel):
    model_config = ConfigDict(title="StartShiftResponseV1")

    route_group_id: UUID
    shift_name: str
    route_group_status: str
    driver_id: int
    driver_name: str
    vehicle_type: str
    driver_status: str
    updated_delivery_count: int
    external_sync_status: str
