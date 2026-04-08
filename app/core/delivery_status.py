from __future__ import annotations

from enum import Enum


class DeliveryExecutionStatus(str, Enum):
    SCHEDULED = "scheduled"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"


_DELIVERY_STATUS_ALIASES: dict[str, DeliveryExecutionStatus] = {
    DeliveryExecutionStatus.SCHEDULED.value: DeliveryExecutionStatus.SCHEDULED,
    "scheduled": DeliveryExecutionStatus.SCHEDULED,
    "schedule": DeliveryExecutionStatus.SCHEDULED,
    DeliveryExecutionStatus.OUT_FOR_DELIVERY.value: DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    "out for delivery": DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    "out-for-delivery": DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    "out_for_delivery": DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    DeliveryExecutionStatus.DELIVERED.value: DeliveryExecutionStatus.DELIVERED,
    "delivered": DeliveryExecutionStatus.DELIVERED,
    "completed": DeliveryExecutionStatus.DELIVERED,
    DeliveryExecutionStatus.FAILED.value: DeliveryExecutionStatus.FAILED,
    "failed": DeliveryExecutionStatus.FAILED,
    "exception": DeliveryExecutionStatus.FAILED,
}


ALLOWED_DELIVERY_STATUS_TRANSITIONS: dict[DeliveryExecutionStatus, set[DeliveryExecutionStatus]] = {
    DeliveryExecutionStatus.SCHEDULED: {
        DeliveryExecutionStatus.OUT_FOR_DELIVERY,
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


def normalize_delivery_execution_status(
    value: str | DeliveryExecutionStatus,
) -> DeliveryExecutionStatus:
    if isinstance(value, DeliveryExecutionStatus):
        return value

    normalized_value = value.strip().lower().replace("-", "_")
    normalized_value = " ".join(normalized_value.split())
    normalized_value = normalized_value.replace(" ", "_")

    try:
        return _DELIVERY_STATUS_ALIASES[normalized_value]
    except KeyError as exc:
        raise ValueError(f"Unknown delivery execution status: {value}") from exc


def validate_delivery_execution_transition(
    current_status: str | DeliveryExecutionStatus,
    new_status: str | DeliveryExecutionStatus,
) -> tuple[DeliveryExecutionStatus, DeliveryExecutionStatus]:
    current = normalize_delivery_execution_status(current_status)
    target = normalize_delivery_execution_status(new_status)

    if target not in ALLOWED_DELIVERY_STATUS_TRANSITIONS[current]:
        raise InvalidStatusTransitionError(current, target)

    return current, target
