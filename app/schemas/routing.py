from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RouteCoordinate(BaseModel):
    model_config = ConfigDict(title="RouteCoordinateV1")

    latitude: float
    longitude: float


class RouteMapWaypoint(BaseModel):
    model_config = ConfigDict(title="RouteMapWaypointV1")

    latitude: float
    longitude: float
    label: str
    address: str | None = None
    sequence: int | None = None
    route_stop_id: UUID | None = None
    delivery_request_id: UUID | None = None
    order_id: int | None = None
    stop_status: str | None = None


class RouteMapResponse(BaseModel):
    model_config = ConfigDict(title="RouteMapResponseV1")

    route_group_id: UUID
    route_group_name: str
    route_group_status: str
    routing_status: str
    provider: str
    warehouse: RouteMapWaypoint
    stops: list[RouteMapWaypoint]
    path: list[RouteCoordinate]
    estimated_distance_km: float | None = None
    estimated_duration_min: int | None = None
