from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

import app.models.db_models  # noqa: F401
from app.api.routes import planning
from app.core.database import Base, SessionLocal, engine
from app.repositories.customer_repository import CustomerRepository
from app.repositories.delivery_request_repository import DeliveryRequestRepository
from app.repositories.planning_repository import PlanningRepository
from app.services.planning_service import PlanningService
from tests.conftest import client


def _clear_persisted_rows() -> None:
    """Delete test data without dropping the shared migrated schema."""
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture(autouse=True)
def reset_planning_db_state():
    try:
        planning.service.close()
    except Exception:
        pass

    _clear_persisted_rows()
    planning.service = PlanningService(SessionLocal())

    yield

    planning.service.close()
    _clear_persisted_rows()

def _seed_delivery_request(
    *,
    order_id: int,
    customer_id: int,
    customer_repo: CustomerRepository,
    request_repo: DeliveryRequestRepository,
    order_type: str = "delivery",
    city: str = "Toronto",
    province: str = "ON",
    postal_code: str = "M5V 1A1",
    add_customer_enrichment: bool = True,
):
    delivery_request = request_repo.create_delivery_request(
        order_id=order_id,
        customer_id=customer_id,
        request_timestamp=datetime(2026, 4, 8, 12, order_id % 60, tzinfo=timezone.utc),
        request_status="received",
        raw_payload={
            "order_id": order_id,
            "customer_id": customer_id,
            "request_timestamp": f"2026-04-08T12:{order_id % 60:02d}:00Z",
            "order_type": order_type,
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

    if add_customer_enrichment:
        customer_repo.save_customer_enrichment(
            delivery_request_id=delivery_request.id,
            raw_payload={"customer_id": customer_id},
            customer_name=f"Customer {customer_id}",
            phone_number="555-0101",
            street="123 Market Street",
            city=city,
            province=province,
            postal_code=postal_code,
            country="CA",
            latitude=43.6532,
            longitude=-79.3832,
            geocode_status="resolved",
        )

    return {"id": str(delivery_request.id), "order_id": delivery_request.order_id}



def test_group_backlog_groups_by_postal_prefix_then_city_province_and_separates_pickups():
    db = SessionLocal()
    try:
        request_repo = DeliveryRequestRepository(db)
        customer_repo = CustomerRepository(db)
        planning_repo = PlanningRepository(db)

        first_delivery = _seed_delivery_request(
            order_id=1001,
            customer_id=501,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Toronto",
            province="ON",
            postal_code="M5V 1A1",
        )
        second_delivery = _seed_delivery_request(
            order_id=1002,
            customer_id=502,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Toronto",
            province="ON",
            postal_code="m5v2b2",
        )
        _seed_delivery_request(
            order_id=1003,
            customer_id=503,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Ottawa",
            province="ON",
            postal_code="",
        )
        _seed_delivery_request(
            order_id=1004,
            customer_id=504,
            customer_repo=customer_repo,
            request_repo=request_repo,
            order_type="pickup",
            city="Toronto",
            province="ON",
            postal_code="M5V 7A1",
        )
        _seed_delivery_request(
            order_id=1005,
            customer_id=505,
            customer_repo=customer_repo,
            request_repo=request_repo,
            add_customer_enrichment=False,
        )
        already_grouped = _seed_delivery_request(
            order_id=1006,
            customer_id=506,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Toronto",
            province="ON",
            postal_code="M4B 1B3",
        )
        route_group = planning_repo.create_route_group(
            name="Existing Group",
            scheduled_date=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
            status="draft",
            zone_code="postal_prefix:M4B",
            total_stops=1,
        )
        planning_repo.add_route_stop(
            route_group_id=route_group.id,
            delivery_request_id=UUID(already_grouped["id"]),
            sequence=1,
            stop_status="planned",
        )
    finally:
        db.close()

    response = client.post("/api/planning/group-backlog")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Backlog grouped deterministically (v1)"
    assert body["total_groups"] == 3
    assert body["total_candidates"] == 4
    assert body["skipped_count"] == 2

    groups_by_key = {group["group_key"]: group for group in body["groups"]}
    assert set(groups_by_key) == {
        "delivery:city_province:OTTAWA:ON",
        "delivery:postal_prefix:M5V",
        "pickup:postal_prefix:M5V",
    }

    postal_group = groups_by_key["delivery:postal_prefix:M5V"]
    assert postal_group["region_source"] == "postal_prefix"
    assert postal_group["request_count"] == 2
    assert [candidate["order_id"] for candidate in postal_group["candidates"]] == [1001, 1002]
    assert [candidate["delivery_request_id"] for candidate in postal_group["candidates"]] == [
        first_delivery["id"],
        second_delivery["id"],
    ]
    assert all(candidate["postal_prefix"] == "M5V" for candidate in postal_group["candidates"])

    fallback_group = groups_by_key["delivery:city_province:OTTAWA:ON"]
    assert fallback_group["region_source"] == "city_province"
    assert fallback_group["request_count"] == 1
    assert fallback_group["candidates"][0]["order_id"] == 1003
    assert fallback_group["candidates"][0]["postal_prefix"] is None

    pickup_group = groups_by_key["pickup:postal_prefix:M5V"]
    assert pickup_group["handling_type"] == "pickup"
    assert pickup_group["request_count"] == 1
    assert pickup_group["candidates"][0]["order_id"] == 1004

    skipped_by_order = {skip["order_id"]: skip["reason"] for skip in body["skipped_requests"]}
    assert skipped_by_order == {
        1005: "missing_customer_enrichment",
        1006: "already_grouped",
    }



def test_schedule_routes_creates_route_groups_with_deterministic_stop_sequence_and_assignment():
    db = SessionLocal()
    try:
        request_repo = DeliveryRequestRepository(db)
        customer_repo = CustomerRepository(db)
        planning_repo = PlanningRepository(db)

        first_delivery = _seed_delivery_request(
            order_id=1001,
            customer_id=501,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Toronto",
            province="ON",
            postal_code="M5V 1A1",
        )
        second_delivery = _seed_delivery_request(
            order_id=1002,
            customer_id=502,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Toronto",
            province="ON",
            postal_code="m5v2b2",
        )
        _seed_delivery_request(
            order_id=1003,
            customer_id=503,
            customer_repo=customer_repo,
            request_repo=request_repo,
            city="Ottawa",
            province="ON",
            postal_code="",
        )

        existing_group = planning_repo.create_route_group(
            name="Existing assigned group",
            scheduled_date=datetime(2026, 4, 8, 8, 0, tzinfo=timezone.utc),
            status="scheduled",
            zone_code="postal_prefix:M4B",
            total_stops=1,
        )
        planning_repo.assign_driver(
            route_group_id=existing_group.id,
            driver_id=1,
            assignment_status="assigned",
        )
    finally:
        db.close()

    response = client.post("/api/planning/schedule")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Route groups scheduled deterministically (v1)"
    assert body["scheduled_group_count"] == 2
    assert body["assigned_group_count"] == 2
    assert body["unassigned_group_count"] == 0

    route_groups_by_key = {group["group_key"]: group for group in body["route_groups"]}
    assert set(route_groups_by_key) == {
        "delivery:city_province:OTTAWA:ON",
        "delivery:postal_prefix:M5V",
    }

    ottawa_group = route_groups_by_key["delivery:city_province:OTTAWA:ON"]
    assert ottawa_group["driver_assignment"]["driver_id"] == 2
    assert ottawa_group["driver_assignment"]["current_load_before_assignment"] == 0
    assert ottawa_group["total_stops"] == 1
    assert ottawa_group["stops"][0]["sequence"] == 1
    assert ottawa_group["stops"][0]["order_id"] == 1003

    postal_group = route_groups_by_key["delivery:postal_prefix:M5V"]
    assert postal_group["driver_assignment"]["driver_id"] == 1
    assert postal_group["driver_assignment"]["current_load_before_assignment"] == 1
    assert postal_group["route_group_status"] == "scheduled"
    assert postal_group["zone_code"] == "postal_prefix:M5V"
    assert [stop["sequence"] for stop in postal_group["stops"]] == [1, 2]
    assert [stop["order_id"] for stop in postal_group["stops"]] == [1001, 1002]
    assert [stop["delivery_request_id"] for stop in postal_group["stops"]] == [
        first_delivery["id"],
        second_delivery["id"],
    ]

    db = SessionLocal()
    try:
        persisted_groups = planning_repo = PlanningRepository(db).list_route_groups()
        created_groups = [group for group in persisted_groups if group.name.startswith("route-group:")]
        assert len(created_groups) == 2
        assert sum(group.total_stops for group in created_groups) == 3
    finally:
        db.close()
