from __future__ import annotations

from uuid import UUID

import app.models.db_models  # noqa: F401
from app.api.routes import intake
from app.core.database import Base, SessionLocal, engine
from app.models.db_models import DeliveryItem, DeliveryRequest, DeliveryRequestSnapshot
from app.services.intake_service import IntakeService
from tests.conftest import client

PAYLOAD = {
    "order_id": 1001,
    "customer_id": 501,
    "request_timestamp": "2026-04-08T12:30:00Z",
    "items": [
        {
            "external_item_id": 9001,
            "item_name": "Mixed Farm Box",
            "quantity": 1,
        },
        {
            "external_item_id": 9002,
            "item_name": "Egg Add-on",
            "quantity": 2,
        },
    ],
}


import pytest


def _clear_persisted_rows() -> None:
    """Delete test data without dropping the shared schema.

    CI runs Alembic migrations once before the test suite. These tests should only
    clear rows they create; dropping tables here breaks later integration tests
    that rely on the migrated schema still existing.
    """
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture(autouse=True)
def reset_intake_db_state():
    try:
        intake.service.close()
    except Exception:
        pass

    _clear_persisted_rows()
    intake.service = IntakeService(SessionLocal())

    yield

    intake.service.close()
    _clear_persisted_rows()


def test_first_create_persists_delivery_request_snapshot_and_items():
    response = client.post("/api/delivery-requests/", json=PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Delivery request persisted (v1)"
    assert body["order_id"] == 1001
    assert body["request_status"] == "received"
    assert UUID(body["delivery_request_id"])

    db = SessionLocal()
    try:
        delivery_requests = db.query(DeliveryRequest).all()
        assert len(delivery_requests) == 1
        delivery_request = delivery_requests[0]
        assert delivery_request.order_id == 1001
        assert delivery_request.customer_id == 501
        assert delivery_request.request_status == "received"

        snapshots = db.query(DeliveryRequestSnapshot).all()
        assert len(snapshots) == 1
        assert snapshots[0].request_payload == PAYLOAD

        items = db.query(DeliveryItem).order_by(DeliveryItem.external_item_id).all()
        assert len(items) == 2
        assert [(item.external_item_id, item.item_name, item.quantity) for item in items] == [
            (9001, "Mixed Farm Box", 1),
            (9002, "Egg Add-on", 2),
        ]
    finally:
        db.close()


def test_duplicate_same_payload_is_idempotent_and_returns_existing_record():
    first_response = client.post("/api/delivery-requests/", json=PAYLOAD)
    second_response = client.post("/api/delivery-requests/", json=PAYLOAD)

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert second_response.json()["message"] == "Delivery request already received (v1)"
    assert second_response.json()["delivery_request_id"] == first_response.json()["delivery_request_id"]

    db = SessionLocal()
    try:
        assert db.query(DeliveryRequest).count() == 1
        assert db.query(DeliveryRequestSnapshot).count() == 1
        assert db.query(DeliveryItem).count() == 2
    finally:
        db.close()


def test_duplicate_conflicting_payload_returns_conflict_without_overwrite():
    create_response = client.post("/api/delivery-requests/", json=PAYLOAD)
    assert create_response.status_code == 201

    conflicting_payload = {
        **PAYLOAD,
        "items": [
            {
                "external_item_id": 9001,
                "item_name": "Mixed Farm Box",
                "quantity": 3,
            }
        ],
    }

    conflict_response = client.post("/api/delivery-requests/", json=conflicting_payload)

    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "detail": "Conflicting delivery request already exists for order_id 1001"
    }

    db = SessionLocal()
    try:
        assert db.query(DeliveryRequest).count() == 1
        snapshot = db.query(DeliveryRequestSnapshot).one()
        assert snapshot.request_payload == PAYLOAD
        items = db.query(DeliveryItem).order_by(DeliveryItem.external_item_id).all()
        assert [(item.external_item_id, item.quantity) for item in items] == [(9001, 1), (9002, 2)]
    finally:
        db.close()
