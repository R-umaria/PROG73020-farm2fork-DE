from __future__ import annotations

from datetime import datetime, timezone

import pytest

import app.models.db_models  # noqa: F401
from app.api.routes import delivery_actions, planning, tracking
from app.core.database import Base, SessionLocal, engine
from app.repositories.customer_repository import CustomerRepository
from app.repositories.delivery_request_repository import DeliveryRequestRepository
from app.repositories.event_repository import EventRepository
from app.services.delivery_actions_service import DeliveryActionsService
from app.services.planning_service import PlanningService
from app.services.tracking_service import TrackingService

def _clear_persisted_rows() -> None:
    """Delete test data without dropping the shared migrated schema."""
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture(autouse=True)
def reset_event_db_state():
    """Isolate event-record tests behind a clean DB and fresh route services."""

    for service in (planning.service, tracking.service, delivery_actions.service):
        try:
            service.close()
        except Exception:
            pass

    _clear_persisted_rows()
    planning.service = PlanningService(SessionLocal())
    tracking.service = TrackingService(SessionLocal())
    delivery_actions.service = DeliveryActionsService(SessionLocal())

    yield

    for service in (planning.service, tracking.service, delivery_actions.service):
        try:
            service.close()
        except Exception:
            pass
    _clear_persisted_rows()


def _seed_delivery_request(order_id: int, customer_id: int):
    db = SessionLocal()
    try:
        request_repo = DeliveryRequestRepository(db)
        customer_repo = CustomerRepository(db)
        delivery_request = request_repo.create_delivery_request(
            order_id=order_id,
            customer_id=customer_id,
            request_timestamp=datetime(2026, 4, 8, 12, order_id % 60, tzinfo=timezone.utc),
            request_status="received",
            raw_payload={
                "order_id": order_id,
                "customer_id": customer_id,
                "request_timestamp": f"2026-04-08T12:{order_id % 60:02d}:00Z",
                "order_type": "delivery",
                "items": [
                    {
                        "external_item_id": 9000 + order_id,
                        "item_name": f"Item {order_id}",
                        "quantity": 1,
                    }
                ],
            },
            items=[
                {
                    "external_item_id": 9000 + order_id,
                    "item_name": f"Item {order_id}",
                    "quantity": 1,
                }
            ],
        )
        customer_repo.save_customer_enrichment(
            delivery_request_id=delivery_request.id,
            raw_payload={"customer_id": customer_id},
            customer_name=f"Customer {customer_id}",
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


def test_event_records_are_written_for_scheduled_dispatched_and_completed_transitions():
    delivery_request = _seed_delivery_request(order_id=1001, customer_id=501)

    planning.service.schedule_routes()
    execution = tracking.service.repo.get_tracking_context_by_order_id(delivery_request["order_id"]).execution
    delivery_actions.service.start_delivery(execution.id)
    delivery_actions.service.complete_delivery(execution.id, received_by="Dock Receiver")

    db = SessionLocal()
    try:
        events = EventRepository(db).list_events()
    finally:
        db.close()

    assert [event.event_type for event in events] == [
        "DeliveryScheduled",
        "DeliveryDispatched",
        "DeliveryCompleted",
    ]
    scheduled_payload = events[0].event_payload
    assert scheduled_payload["order_id"] == 1001
    assert scheduled_payload["delivery_status"] == "scheduled"
    assert scheduled_payload["route_group_id"] is not None
    assert scheduled_payload["route_stop_id"] is not None
    assert scheduled_payload["driver_id"] == 1
    assert scheduled_payload["assignment_status"] == "assigned"

    dispatched_payload = events[1].event_payload
    assert dispatched_payload["previous_status"] == "scheduled"
    assert dispatched_payload["delivery_status"] == "out_for_delivery"
    assert dispatched_payload["changed_by"] == "driver"

    completed_payload = events[2].event_payload
    assert completed_payload["previous_status"] == "out_for_delivery"
    assert completed_payload["delivery_status"] == "delivered"


def test_failed_transition_writes_delivery_failed_event_record():
    delivery_request = _seed_delivery_request(order_id=1002, customer_id=502)

    planning.service.schedule_routes()
    execution = tracking.service.repo.get_tracking_context_by_order_id(delivery_request["order_id"]).execution
    delivery_actions.service.fail_delivery(
        execution.id,
        exception_type="customer_unavailable",
        description="Customer unavailable at doorstep",
        retry_allowed=True,
    )

    db = SessionLocal()
    try:
        events = EventRepository(db).list_events()
    finally:
        db.close()

    assert [event.event_type for event in events] == [
        "DeliveryScheduled",
        "DeliveryFailed",
    ]
    failed_payload = events[-1].event_payload
    assert failed_payload["order_id"] == 1002
    assert failed_payload["previous_status"] == "scheduled"
    assert failed_payload["delivery_status"] == "failed"
    assert failed_payload["reason"] == "Customer unavailable at doorstep"
