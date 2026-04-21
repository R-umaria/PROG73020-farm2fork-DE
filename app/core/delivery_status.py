from __future__ import annotations

from enum import Enum


class DeliveryExecutionStatus(str, Enum):
    SCHEDULED = "scheduled"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"


_DELIVERY_STATUS_ALIASES: dict[str, DeliveryExecutionStatus] = {
    DeliveryExecutionStatus.SCHEDULED.value: DeliveryExecutionStatus.SCHEDULED,
    "schedule": DeliveryExecutionStatus.SCHEDULED,
    DeliveryExecutionStatus.READY_FOR_PICKUP.value: DeliveryExecutionStatus.READY_FOR_PICKUP,
    "available_for_pickup": DeliveryExecutionStatus.READY_FOR_PICKUP,
    "picked_up": DeliveryExecutionStatus.READY_FOR_PICKUP,
    DeliveryExecutionStatus.OUT_FOR_DELIVERY.value: DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    "out for delivery": DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    "out-for-delivery": DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    DeliveryExecutionStatus.DELIVERED.value: DeliveryExecutionStatus.DELIVERED,
    "completed": DeliveryExecutionStatus.DELIVERED,
    DeliveryExecutionStatus.FAILED.value: DeliveryExecutionStatus.FAILED,
    "exception": DeliveryExecutionStatus.FAILED,
}


ALLOWED_DELIVERY_STATUS_TRANSITIONS: dict[DeliveryExecutionStatus, set[DeliveryExecutionStatus]] = {
    DeliveryExecutionStatus.SCHEDULED: {
        DeliveryExecutionStatus.OUT_FOR_DELIVERY,
        DeliveryExecutionStatus.FAILED,
    },
    DeliveryExecutionStatus.READY_FOR_PICKUP: {
        DeliveryExecutionStatus.DELIVERED,
        DeliveryExecutionStatus.FAILED,
    },
    DeliveryExecutionStatus.OUT_FOR_DELIVERY: {
        DeliveryExecutionStatus.DELIVERED,
        DeliveryExecutionStatus.FAILED,
    },
    DeliveryExecutionStatus.DELIVERED: set(),
    DeliveryExecutionStatus.FAILED: set(),
}


INITIAL_DELIVERY_EXECUTION_STATUS = DeliveryExecutionStatus.SCHEDULED


class InvalidStatusTransitionError(ValueError):
    def __init__(
        self,
        current_status: str | DeliveryExecutionStatus,
        new_status: str | DeliveryExecutionStatus,
    ) -> None:
        normalized_current_status = normalize_delivery_execution_status(current_status)
        normalized_new_status = normalize_delivery_execution_status(new_status)
        super().__init__(
            "Invalid delivery execution status transition: "
            f"{normalized_current_status.value} -> {normalized_new_status.value}"
        )
        self.current_status = normalized_current_status
        self.new_status = normalized_new_status


def normalize_delivery_execution_status(status: str | DeliveryExecutionStatus) -> DeliveryExecutionStatus:
    if isinstance(status, DeliveryExecutionStatus):
        return status

    normalized_key = str(status).strip().lower()
    if normalized_key not in _DELIVERY_STATUS_ALIASES:
        raise ValueError(f"Unsupported delivery execution status: {status}")
    return _DELIVERY_STATUS_ALIASES[normalized_key]


def validate_delivery_execution_transition(
    current_status: str | DeliveryExecutionStatus,
    new_status: str | DeliveryExecutionStatus,
) -> tuple[DeliveryExecutionStatus, DeliveryExecutionStatus]:
    current = normalize_delivery_execution_status(current_status)
    target = normalize_delivery_execution_status(new_status)

    if target not in ALLOWED_DELIVERY_STATUS_TRANSITIONS[current]:
        raise InvalidStatusTransitionError(current, target)

    return current, target
