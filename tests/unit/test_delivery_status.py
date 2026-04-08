from app.core.delivery_status import (
    DeliveryExecutionStatus,
    InvalidStatusTransitionError,
    normalize_delivery_execution_status,
    validate_delivery_execution_transition,
)


def test_normalize_delivery_status_accepts_legacy_values():
    assert normalize_delivery_execution_status("Out for Delivery") == DeliveryExecutionStatus.OUT_FOR_DELIVERY
    assert normalize_delivery_execution_status("completed") == DeliveryExecutionStatus.DELIVERED


def test_validate_delivery_execution_transition_allows_expected_path():
    current, target = validate_delivery_execution_transition(
        DeliveryExecutionStatus.SCHEDULED,
        DeliveryExecutionStatus.OUT_FOR_DELIVERY,
    )

    assert current == DeliveryExecutionStatus.SCHEDULED
    assert target == DeliveryExecutionStatus.OUT_FOR_DELIVERY


def test_validate_delivery_execution_transition_rejects_terminal_transition():
    try:
        validate_delivery_execution_transition(
            DeliveryExecutionStatus.DELIVERED,
            DeliveryExecutionStatus.OUT_FOR_DELIVERY,
        )
    except InvalidStatusTransitionError as exc:
        assert str(exc) == "Invalid delivery execution status transition: delivered -> out_for_delivery"
    else:
        raise AssertionError("Expected InvalidStatusTransitionError")
