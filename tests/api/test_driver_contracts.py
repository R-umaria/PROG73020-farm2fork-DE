from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

import app.models.db_models  # noqa: F401
from app.api.routes import driver, drivers
from app.core.database import Base, SessionLocal, engine
from app.integrations.errors import UpstreamBadResponseError, UpstreamTimeoutError
from app.repositories.customer_repository import CustomerRepository
from app.repositories.delivery_request_repository import DeliveryRequestRepository
from app.repositories.planning_repository import PlanningRepository
from app.schemas.driver import DriverSummaryResponse
from app.services.driver_service import DriverService
from tests.conftest import client

def _clear_persisted_rows() -> None:
    """Delete test data without dropping the shared migrated schema."""
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
            
@pytest.fixture(autouse=True)
def reset_driver_contract_state():
    for route_module in (driver, drivers):
        try:
            route_module.service.close()
        except Exception:

            pass

    _clear_persisted_rows()
    driver.service = DriverService(SessionLocal())
    drivers.service = DriverService(SessionLocal())

    yield

    for route_module in (driver, drivers):
        route_module.service.close()
    _clear_persisted_rows()


def _seed_assigned_route_stop(*, driver_id: int = 2) -> UUID:
    db = SessionLocal()
    try:
        request_repo = DeliveryRequestRepository(db)
        customer_repo = CustomerRepository(db)
        planning_repo = PlanningRepository(db)

        delivery_request = request_repo.create_delivery_request(
            order_id=1001,
            customer_id=501,
            request_timestamp=datetime(2026, 4, 8, 12, 30, tzinfo=timezone.utc),
            request_status="received",
            raw_payload={
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
            raw_payload={"customer_id": 501},
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
        route_group = planning_repo.create_route_group(
            name="route-group:delivery:postal_prefix:M5V:20260408T123000Z",
            scheduled_date=datetime(2026, 4, 8, 12, 30, tzinfo=timezone.utc),
            status="scheduled",
            zone_code="postal_prefix:M5V",
            total_stops=1,
        )
        route_stop = planning_repo.add_route_stop(
            route_group_id=route_group.id,
            delivery_request_id=delivery_request.id,
            sequence=1,
            estimated_arrival=datetime(2026, 4, 8, 12, 30, tzinfo=timezone.utc),
            stop_status="planned",
        )
        planning_repo.assign_driver(
            route_group_id=route_group.id,
            driver_id=driver_id,
            assignment_status="assigned",
        )
        return route_stop.id
    finally:
        db.close()


def test_driver_collection_routes_use_consistent_v1_shape(monkeypatch):
    roster = [
        DriverSummaryResponse(
            driver_id=2,
            driver_name="Sam Patel",
            vehicle_type="Bike",
            driver_status="available",
        )
    ]

    monkeypatch.setattr(drivers.service.client, "list_drivers", lambda: roster)
    monkeypatch.setattr(driver.service.client, "list_drivers", lambda: roster)

    plural_response = client.get("/api/drivers/")
    alias_response = client.get("/api/driver/")

    assert plural_response.status_code == 200
    assert alias_response.status_code == 200
    assert plural_response.json() == alias_response.json() == [
        {
            "driver_id": 2,
            "driver_name": "Sam Patel",
            "vehicle_type": "Bike",
            "driver_status": "available",
        }
    ]


def test_driver_schedule_returns_consistent_shape_and_complete_stop_updates_status(monkeypatch):
    route_stop_id = _seed_assigned_route_stop(driver_id=2)
    upstream_driver = DriverSummaryResponse(
        driver_id=2,
        driver_name="Sam Patel",
        vehicle_type="Bike",
        driver_status="available",
    )

    monkeypatch.setattr(driver.service.client, "get_driver", lambda driver_id: upstream_driver)

    schedule_response = client.get("/api/driver/schedule/today/2")

    assert schedule_response.status_code == 200
    body = schedule_response.json()
    assert body["driver_id"] == 2
    assert body["driver_name"] == "Sam Patel"
    assert body["vehicle_type"] == "Bike"
    assert body["driver_status"] == "available"
    assert len(body["stops"]) == 1
    stop = body["stops"][0]
    assert stop["route_stop_id"] == str(route_stop_id)
    assert UUID(stop["route_group_id"])
    assert UUID(stop["delivery_request_id"])
    assert stop["order_id"] == 1001
    assert stop["sequence"] == 1
    assert stop["stop_status"] == "planned"
    assert stop["estimated_arrival"].startswith("2026-04-08T12:30:00")
    assert stop["address"] == "123 Market Street, Toronto, ON, M5V 1A1, CA"

    complete_response = client.post(f"/api/driver/stops/{route_stop_id}/complete")

    assert complete_response.status_code == 200
    assert complete_response.json() == {
        "route_stop_id": str(route_stop_id),
        "stop_status": "completed",
        "message": "Route stop marked completed (v1)",
    }


def test_driver_routes_map_timeout_and_bad_upstream_response(monkeypatch):
    monkeypatch.setattr(
        drivers.service.client,
        "list_drivers",
        lambda: (_ for _ in ()).throw(UpstreamTimeoutError("Driver Service request timed out")),
    )
    timeout_response = client.get("/api/drivers/")
    assert timeout_response.status_code == 504
    assert timeout_response.json() == {"detail": "Driver Service request timed out"}

    monkeypatch.setattr(
        driver.service.client,
        "get_driver",
        lambda driver_id: (_ for _ in ()).throw(
            UpstreamBadResponseError("Driver Service returned an invalid driver roster response")
        ),
    )
    bad_response = client.get("/api/driver/schedule/today/2")
    assert bad_response.status_code == 502
    assert bad_response.json() == {"detail": "Driver Service returned an invalid driver roster response"}
