from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

import app.models.db_models  # noqa: F401
from app.api.routes import intake
from app.core.database import Base, SessionLocal, engine
from app.integrations.customer_module_client import CustomerAddress, CustomerRecord
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)
from app.integrations.geocoding_client import GeocodeResult
from app.models.db_models import CustomerDetails, CustomerDetailsSnapshot
from app.services.intake_service import IntakeService
from tests.conftest import client

INTAKE_PAYLOAD = {
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


def _clear_persisted_rows() -> None:
    """Delete test data without dropping the shared migrated schema.

    CI applies Alembic migrations once before the test suite. These tests must
    clean up only their rows so later tests still see the full baseline schema.
    """
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture(autouse=True)
def reset_customer_sync_db_state():
    try:
        intake.service.close()
    except Exception:
        pass

    _clear_persisted_rows()
    intake.service = IntakeService(SessionLocal())

    yield

    intake.service.close()
    _clear_persisted_rows()


def _create_delivery_request() -> str:
    response = client.post("/api/delivery-requests/", json=INTAKE_PAYLOAD)
    assert response.status_code == 201
    return response.json()["delivery_request_id"]


def test_customer_sync_success_persists_customer_details_and_snapshot(monkeypatch):
    delivery_request_id = _create_delivery_request()

    def fake_get_customer_details(customer_id: int) -> CustomerRecord:
        assert customer_id == 501
        return CustomerRecord(
            customer_id=501,
            customer_name="Jane Doe",
            phone_number="555-0101",
            address=CustomerAddress(
                street="123 Market Street",
                city="Toronto",
                province="ON",
                postal_code="M5V 1A1",
                country="CA",
            ),
        )

    def fake_geocode_address(**kwargs) -> GeocodeResult:
        assert kwargs == {
            "street": "123 Market Street",
            "city": "Toronto",
            "province": "ON",
            "postal_code": "M5V 1A1",
            "country": "CA",
        }
        return GeocodeResult(latitude=43.6532, longitude=-79.3832)

    monkeypatch.setattr(intake.service.customer_client, "get_customer_details", fake_get_customer_details)
    monkeypatch.setattr(intake.service.geocoding_client, "geocode_address", fake_geocode_address)

    response = client.post(f"/api/delivery-requests/{delivery_request_id}/customer-sync")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Customer details synced (v1)",
        "delivery_request_id": delivery_request_id,
        "sync_status": "completed",
    }

    db = SessionLocal()
    try:
        customer_details = db.query(CustomerDetails).one()
        assert customer_details.customer_name == "Jane Doe"
        assert customer_details.phone_number == "555-0101"
        assert customer_details.street == "123 Market Street"
        assert customer_details.city == "Toronto"
        assert customer_details.province == "ON"
        assert customer_details.postal_code == "M5V 1A1"
        assert customer_details.country == "CA"
        assert customer_details.latitude == Decimal("43.6532000")
        assert customer_details.longitude == Decimal("-79.3832000")
        assert customer_details.geocode_status == "resolved"

        snapshot = db.query(CustomerDetailsSnapshot).one()
        assert snapshot.customer_payload == {
            "customer_id": 501,
            "customer_name": "Jane Doe",
            "phone_number": "555-0101",
            "address": {
                "street": "123 Market Street",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V 1A1",
                "country": "CA",
            },
        }
    finally:
        db.close()


def test_customer_sync_maps_timeout_to_504_without_persisting_customer_data(monkeypatch):
    delivery_request_id = _create_delivery_request()

    def fake_get_customer_details(customer_id: int):
        raise UpstreamTimeoutError("Customer & Subscriptions request timed out")

    monkeypatch.setattr(intake.service.customer_client, "get_customer_details", fake_get_customer_details)

    response = client.post(f"/api/delivery-requests/{delivery_request_id}/customer-sync")

    assert response.status_code == 504
    assert response.json() == {"detail": "Customer & Subscriptions request timed out"}

    db = SessionLocal()
    try:
        assert db.query(CustomerDetails).count() == 0
        assert db.query(CustomerDetailsSnapshot).count() == 0
    finally:
        db.close()


def test_customer_sync_maps_invalid_upstream_response_to_502(monkeypatch):
    delivery_request_id = _create_delivery_request()

    def fake_get_customer_details(customer_id: int) -> CustomerRecord:
        return CustomerRecord(
            customer_id=501,
            customer_name="Jane Doe",
            phone_number="555-0101",
            address=CustomerAddress(
                street="123 Market Street",
                city="Toronto",
                province="ON",
                postal_code="M5V 1A1",
                country="CA",
            ),
        )

    def fake_geocode_address(**kwargs):
        raise UpstreamBadResponseError("Geocoding service returned an invalid geocode response")

    monkeypatch.setattr(intake.service.customer_client, "get_customer_details", fake_get_customer_details)
    monkeypatch.setattr(intake.service.geocoding_client, "geocode_address", fake_geocode_address)

    response = client.post(f"/api/delivery-requests/{delivery_request_id}/customer-sync")

    assert response.status_code == 502
    assert response.json() == {"detail": "Geocoding service returned an invalid geocode response"}

    db = SessionLocal()
    try:
        assert db.query(CustomerDetails).count() == 0
        assert db.query(CustomerDetailsSnapshot).count() == 0
    finally:
        db.close()


def test_customer_sync_maps_not_found_to_404(monkeypatch):
    delivery_request_id = _create_delivery_request()

    def fake_get_customer_details(customer_id: int):
        raise UpstreamNotFoundError("Customer 501 was not found in Customer & Subscriptions")

    monkeypatch.setattr(intake.service.customer_client, "get_customer_details", fake_get_customer_details)

    response = client.post(f"/api/delivery-requests/{delivery_request_id}/customer-sync")

    assert response.status_code == 404
    assert response.json() == {"detail": "Customer 501 was not found in Customer & Subscriptions"}
