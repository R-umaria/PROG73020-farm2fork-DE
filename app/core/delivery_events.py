"""Canonical delivery execution event names and helpers."""

from __future__ import annotations

from enum import Enum

from app.core.delivery_status import DeliveryExecutionStatus, normalize_delivery_execution_status


class DeliveryEventType(str, Enum):
    DELIVERY_SCHEDULED = "DeliveryScheduled"
    DELIVERY_READY_FOR_PICKUP = "DeliveryReadyForPickup"
    DELIVERY_DISPATCHED = "DeliveryDispatched"
    DELIVERY_COMPLETED = "DeliveryCompleted"
    DELIVERY_FAILED = "DeliveryFailed"


_EVENT_TYPE_BY_STATUS: dict[DeliveryExecutionStatus, DeliveryEventType] = {
    DeliveryExecutionStatus.SCHEDULED: DeliveryEventType.DELIVERY_SCHEDULED,
    DeliveryExecutionStatus.READY_FOR_PICKUP: DeliveryEventType.DELIVERY_READY_FOR_PICKUP,
    DeliveryExecutionStatus.OUT_FOR_DELIVERY: DeliveryEventType.DELIVERY_DISPATCHED,
    DeliveryExecutionStatus.DELIVERED: DeliveryEventType.DELIVERY_COMPLETED,
    DeliveryExecutionStatus.FAILED: DeliveryEventType.DELIVERY_FAILED,
}


def delivery_event_type_for_status(status: str | DeliveryExecutionStatus) -> DeliveryEventType:
    return _EVENT_TYPE_BY_STATUS[normalize_delivery_execution_status(status)]
