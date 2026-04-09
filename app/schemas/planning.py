from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BacklogPlanningCandidate(BaseModel):
    model_config = ConfigDict(title="BacklogPlanningCandidateV1")

    delivery_request_id: UUID
    order_id: int
    customer_id: int
    handling_type: Literal["delivery", "pickup"]
    region_key: str
    region_source: Literal["postal_prefix", "city_province"]
    postal_prefix: str | None = None
    city: str
    province: str
    request_timestamp: datetime


class BacklogPlanningGroup(BaseModel):
    model_config = ConfigDict(title="BacklogPlanningGroupV1")

    group_key: str
    handling_type: Literal["delivery", "pickup"]
    region_key: str
    region_source: Literal["postal_prefix", "city_province"]
    request_count: int
    candidates: list[BacklogPlanningCandidate]


class BacklogPlanningSkip(BaseModel):
    model_config = ConfigDict(title="BacklogPlanningSkipV1")

    delivery_request_id: UUID
    order_id: int
    reason: str


class GroupBacklogResponse(BaseModel):
    model_config = ConfigDict(title="GroupBacklogResponseV1")

    message: str
    total_groups: int
    total_candidates: int
    skipped_count: int
    groups: list[BacklogPlanningGroup]
    skipped_requests: list[BacklogPlanningSkip]


class ScheduledDriverAssignment(BaseModel):
    model_config = ConfigDict(title="ScheduledDriverAssignmentV1")

    driver_id: int
    driver_name: str
    vehicle_type: str
    assignment_status: str
    current_load_before_assignment: int


class ScheduledRouteStop(BaseModel):
    model_config = ConfigDict(title="ScheduledRouteStopV1")

    route_stop_id: UUID
    delivery_request_id: UUID
    order_id: int
    sequence: int
    stop_status: str
    estimated_arrival: datetime | None = None


class ScheduledRouteGroup(BaseModel):
    model_config = ConfigDict(title="ScheduledRouteGroupV1")

    route_group_id: UUID
    group_key: str
    route_group_name: str
    handling_type: Literal["delivery", "pickup"]
    zone_code: str
    scheduled_date: datetime
    route_group_status: str
    total_stops: int
    driver_assignment: ScheduledDriverAssignment | None = None
    stops: list[ScheduledRouteStop]


class ScheduleRoutesResponse(BaseModel):
    model_config = ConfigDict(title="ScheduleRoutesResponseV1")

    message: str
    scheduled_group_count: int
    assigned_group_count: int
    unassigned_group_count: int
    route_groups: list[ScheduledRouteGroup]


class PlanningResponse(BaseModel):
    message: str
