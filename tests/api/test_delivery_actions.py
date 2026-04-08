from types import SimpleNamespace
from uuid import uuid4

from app.api.routes import delivery_actions
from app.core.delivery_status import InvalidStatusTransitionError
from tests.conftest import client


def test_start_delivery_returns_canonical_status(monkeypatch):
    delivery_execution_id = uuid4()

    def fake_start_delivery(requested_id):
        assert requested_id == delivery_execution_id
        return SimpleNamespace(
            id=delivery_execution_id,
            current_status="out_for_delivery",
        )

    monkeypatch.setattr(delivery_actions.service, "start_delivery", fake_start_delivery)

    response = client.post(f"/api/deliveries/{delivery_execution_id}/start")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(delivery_execution_id),
        "status": "out_for_delivery",
    }


def test_complete_delivery_returns_conflict_for_invalid_transition(monkeypatch):
    delivery_execution_id = uuid4()

    def fake_complete_delivery(*args, **kwargs):
        raise InvalidStatusTransitionError(
            current_status="delivered",
            new_status="delivered",
        )

    monkeypatch.setattr(delivery_actions.service, "complete_delivery", fake_complete_delivery)

    response = client.post(
        f"/api/deliveries/{delivery_execution_id}/complete",
        json={"received_by": "Dock Receiver"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Invalid delivery execution status transition: delivered -> delivered"
    }
