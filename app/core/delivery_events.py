"""Canonical delivery execution event names and helpers.

These events are the internal placeholder/outbox records used until a real
message bus exists. They intentionally mirror upstream-facing event semantics so
emission points remain explicit and testable.
"""

from __future__ import annotations

from enum import Enum

from app.core.delivery_status import DeliveryExecutionStatus, normalize_delivery_execution_status


class DeliveryEventType(str, Enum):
    """Supported delivery execution domain events."""

    DELIVERY_SCHEDULED = "DeliveryScheduled"
    DELIVERY_DISPATCHED = "DeliveryDispatched"
    DELIVERY_COMPLETED = "DeliveryCompleted"
    DELIVERY_FAILED = "DeliveryFailed"


_EVENT_TYPE_BY_STATUS: dict[DeliveryExecutionStatus, DeliveryEventType] = {
    DeliveryExecutionStatus.SCHEDULED: DeliveryEventType.DELIVERY_SCHEDULED,
    DeliveryExecutionStatus.OUT_FOR_DELIVERY: DeliveryEventType.DELIVERY_DISPATCHED,
    DeliveryExecutionStatus.DELIVERED: DeliveryEventType.DELIVERY_COMPLETED,
    DeliveryExecutionStatus.FAILED: DeliveryEventType.DELIVERY_FAILED,
}


def delivery_event_type_for_status(status: str | DeliveryExecutionStatus) -> DeliveryEventType:
    """Map the canonical execution status model to its emitted event name."""

    return _EVENT_TYPE_BY_STATUS[normalize_delivery_execution_status(status)]
