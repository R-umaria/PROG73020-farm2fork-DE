from app.core.delivery_events import DeliveryEventType, delivery_event_type_for_status


def test_delivery_event_type_mapping_uses_canonical_status_model():
    assert delivery_event_type_for_status("scheduled") is DeliveryEventType.DELIVERY_SCHEDULED
    assert delivery_event_type_for_status("out_for_delivery") is DeliveryEventType.DELIVERY_DISPATCHED
    assert delivery_event_type_for_status("delivered") is DeliveryEventType.DELIVERY_COMPLETED
    assert delivery_event_type_for_status("failed") is DeliveryEventType.DELIVERY_FAILED


def test_delivery_event_type_mapping_normalizes_supported_legacy_status_strings():
    assert delivery_event_type_for_status("out for delivery") is DeliveryEventType.DELIVERY_DISPATCHED
    assert delivery_event_type_for_status("completed") is DeliveryEventType.DELIVERY_COMPLETED
