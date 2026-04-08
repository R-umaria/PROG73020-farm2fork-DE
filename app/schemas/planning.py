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


class PlanningResponse(BaseModel):
    message: str
