from __future__ import annotations

from datetime import datetime, timezone

import pytest

import app.models.db_models  # noqa: F401
from app.api.routes import delivery_actions, planning, tracking
from app.core.database import Base, SessionLocal, engine
from app.repositories.customer_repository import CustomerRepository
from app.repositories.delivery_request_repository import DeliveryRequestRepository
from app.services.delivery_actions_service import DeliveryActionsService
from app.services.planning_service import PlanningService
from app.services.tracking_service import TrackingService
from tests.conftest import client


@pytest.fixture(autouse=True)
def reset_tracking_db_state():
    """Rebuild the test DB and refresh singleton-style route services."""

    for service in (planning.service, tracking.service, delivery_actions.service):
        try:
            service.close()
        except Exception:
            pass

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    planning.service = PlanningService(SessionLocal())
    tracking.service = TrackingService(SessionLocal())
    delivery_actions.service = DeliveryActionsService(SessionLocal())

    yield

    for service in (planning.service, tracking.service, delivery_actions.service):
        try:
            service.close()
        except Exception:
            pass
    Base.metadata.drop_all(bind=engine)


def _seed_delivery_request(order_id: int = 1001, customer_id: int = 501):
    db = SessionLocal()
    try:
        request_repo = DeliveryRequestRepository(db)
        customer_repo = CustomerRepository(db)
        delivery_request = request_repo.create_delivery_request(
            order_id=order_id,
            customer_id=customer_id,
            request_timestamp=datetime(2026, 4, 8, 12, 30, tzinfo=timezone.utc),
            request_status="received",
            raw_payload={
                "order_id": order_id,
                "customer_id": customer_id,
                "request_timestamp": "2026-04-08T12:30:00Z",
                "order_type": "delivery",
                "items": [
                    {
                        "external_item_id": 9001,
                        "item_name": "Mixed Farm Box",
                        "quantity": 1,
                    }
                ],
            },
            items=[
                {
                    "external_item_id": 9001,
                    "item_name": "Mixed Farm Box",
                    "quantity": 1,
                }
            ],
        )
        customer_repo.save_customer_enrichment(
            delivery_request_id=delivery_request.id,
            raw_payload={"customer_id": customer_id},
            customer_name="Jane Doe",
            phone_number="555-0101",
            street="123 Market Street",
            city="Toronto",
            province="ON",
            postal_code="M5V 1A1",
            country="CA",
            latitude=43.6532,
            longitude=-79.3832,
            geocode_status="resolved",
        )
        return {"id": str(delivery_request.id), "order_id": delivery_request.order_id}
    finally:
        db.close()


def test_tracking_status_reads_persisted_execution_and_history():
    delivery_request = _seed_delivery_request()

    schedule_response = client.post("/api/planning/schedule")
    assert schedule_response.status_code == 200

    execution = tracking.service.repo.get_tracking_context_by_order_id(delivery_request["order_id"]).execution
    start_response = client.post(f"/api/deliveries/{execution.id}/start")
    assert start_response.status_code == 200

    response = client.get(f"/api/delivery-status/{delivery_request['order_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == 1001
    assert body["customer_id"] == 501
    assert body["delivery_request_id"] == delivery_request["id"]
    assert body["delivery_execution_id"] == str(execution.id)
    assert body["delivery_status"] == "out_for_delivery"
    assert body["latest_status_reason"] == "Driver started route"
    assert body["route_group_status"] == "scheduled"
    assert body["stop_status"] == "planned"
    assert body["assigned_driver_id"] == 1
    assert body["assignment_status"] == "assigned"
    assert body["route_group_id"]
    assert body["route_stop_id"]
    assert body["estimated_arrival"] == "2026-04-08T12:30:00Z"
    assert body["dispatched_at"].endswith("Z")
    assert body["out_for_delivery_at"].endswith("Z")
    assert [entry["status"] for entry in body["status_history"]] == [
        "scheduled",
        "out_for_delivery",
    ]


def test_tracking_status_returns_404_when_execution_does_not_exist():
    response = client.get("/api/delivery-status/9999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Tracked delivery status not found for order_id 9999"
    }
