from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.delivery_status import DeliveryExecutionStatus


class DeliveryStatusHistoryEntry(BaseModel):
    """Status transition timeline entry exposed by the tracking API."""

    model_config = ConfigDict(title="DeliveryStatusHistoryEntryV1")

    status: DeliveryExecutionStatus
    changed_at: datetime
    changed_by: str | None = None
    reason: str | None = None


class DeliveryStatusResponse(BaseModel):
    """DB-backed v1 tracking response for upstream consumers and driver UI."""

    model_config = ConfigDict(title="DeliveryStatusResponseV1")

    order_id: int
    customer_id: int | None = None
    delivery_request_id: UUID | None = None
    delivery_execution_id: UUID
    delivery_status: DeliveryExecutionStatus
    latest_status_at: datetime | None = None
    latest_status_reason: str | None = None
    route_group_id: UUID | None = None
    route_group_status: str | None = None
    route_stop_id: UUID | None = None
    stop_sequence: int | None = None
    stop_status: str | None = None
    estimated_arrival: datetime | None = None
    scheduled_for: datetime | None = None
    assigned_driver_id: int | None = None
    assignment_status: str | None = None
    dispatched_at: datetime | None = None
    out_for_delivery_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    status_history: list[DeliveryStatusHistoryEntry] = Field(default_factory=list)
