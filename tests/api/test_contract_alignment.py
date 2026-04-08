from datetime import datetime, timezone
from uuid import uuid4

from app.api.routes import deliveries, intake, tracking
from tests.conftest import client


V1_PAYLOAD = {
    "order_id": 1001,
    "customer_id": 501,
    "request_timestamp": "2026-04-08T12:30:00Z",
    "items": [
        {
            "external_item_id": 9001,
            "item_name": "Mixed Farm Box",
            "quantity": 1,
        }
    ],
}


def test_intake_v1_request_and_response_shape(monkeypatch):
    delivery_request_id = uuid4()

    def fake_receive_delivery_request(payload):
        assert payload.order_id == 1001
        assert payload.customer_id == 501
        assert payload.request_timestamp == datetime(2026, 4, 8, 12, 30, tzinfo=timezone.utc)
        assert len(payload.items) == 1
        assert payload.items[0].external_item_id == 9001
        return {
            "message": "Delivery request persisted (v1)",
            "order_id": payload.order_id,
            "request_status": "received",
            "delivery_request_id": delivery_request_id,
        }

    monkeypatch.setattr(intake.service, "receive_delivery_request", fake_receive_delivery_request)

    response = client.post("/api/delivery-requests/", json=V1_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        "message": "Delivery request persisted (v1)",
        "order_id": 1001,
        "request_status": "received",
        "delivery_request_id": str(delivery_request_id),
    }


def test_manual_delivery_create_uses_delivery_request_v1_shape(monkeypatch):
    delivery_request_id = uuid4()

    def fake_create_delivery(payload):
        assert payload.order_id == 1001
        assert payload.customer_id == 501
        assert payload.request_timestamp == datetime(2026, 4, 8, 12, 30, tzinfo=timezone.utc)
        assert payload.items[0].item_name == "Mixed Farm Box"
        return {
            "id": delivery_request_id,
            "order_id": payload.order_id,
            "customer_id": payload.customer_id,
            "request_timestamp": payload.request_timestamp,
            "items": [item.model_dump() for item in payload.items],
            "request_status": "received",
            "created_at": datetime(2026, 4, 8, 12, 30, 5, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 4, 8, 12, 30, 5, tzinfo=timezone.utc),
        }

    monkeypatch.setattr(deliveries.service, "create_delivery", fake_create_delivery)

    response = client.post("/api/deliveries/", json=V1_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        "id": str(delivery_request_id),
        "order_id": 1001,
        "customer_id": 501,
        "request_timestamp": "2026-04-08T12:30:00Z",
        "items": [
            {
                "external_item_id": 9001,
                "item_name": "Mixed Farm Box",
                "quantity": 1,
            }
        ],
        "request_status": "received",
        "created_at": "2026-04-08T12:30:05Z",
        "updated_at": "2026-04-08T12:30:05Z",
    }


def test_tracking_v1_response_shape(monkeypatch):
    delivery_execution_id = uuid4()

    def fake_get_status(order_id):
        assert order_id == 1001
        return {
            "order_id": order_id,
            "delivery_status": "scheduled",
            "delivery_execution_id": delivery_execution_id,
        }

    monkeypatch.setattr(tracking.service, "get_status", fake_get_status)

    response = client.get("/api/delivery-status/1001")

    assert response.status_code == 200
    assert response.json() == {
        "order_id": 1001,
        "delivery_status": "scheduled",
        "delivery_execution_id": str(delivery_execution_id),
        "status_history": [],
    }
