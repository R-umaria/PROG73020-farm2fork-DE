from datetime import datetime

from app.core.database import SessionLocal
from app.repositories import (
    CustomerRepository,
    DeliveryRequestRepository,
    ExecutionRepository,
    PlanningRepository,
)


def run():
    db = SessionLocal()

    try:
        delivery_repo = DeliveryRequestRepository(db)
        customer_repo = CustomerRepository(db)
        planning_repo = PlanningRepository(db)
        execution_repo = ExecutionRepository(db)

        # 1. Create delivery request + snapshot + items
        delivery_request = delivery_repo.create_delivery_request(
            order_id=1001,
            customer_id=501,
            request_timestamp=datetime.utcnow(),
            request_status="RECEIVED",
            raw_payload={"source": "order-service", "note": "demo request"},
            items=[
                {"external_item_id": 1, "item_name": "Milk", "quantity": 2},
                {"external_item_id": 2, "item_name": "Bread", "quantity": 1},
            ],
        )

        # 2. Customer enrichment
        customer_repo.save_customer_enrichment(
            delivery_request_id=delivery_request.id,
            raw_payload={"api": "customer-service"},
            customer_name="Alex Johnson",
            phone_number="1234567890",
            street="100 Queen St W",
            city="Toronto",
            province="ON",
            postal_code="M5H 2N2",
            country="Canada",
        )

        # 3. Planning (route + stop + driver)
        route = planning_repo.create_route_group(
            name="Morning Route",
            scheduled_date=datetime.utcnow(),
            status="PLANNED",
            zone_code="DT-1",
        )

        planning_repo.add_route_stop(
            route_group_id=route.id,
            delivery_request_id=delivery_request.id,
            sequence=1,
            stop_status="PENDING",
        )

        planning_repo.assign_driver(
            route_group_id=route.id,
            driver_id=1,
            assignment_status="ASSIGNED",
        )

        # 4. Execution
        execution = execution_repo.create_execution(
            delivery_request_id=delivery_request.id,
            current_status="SCHEDULED",
        )

        execution_repo.update_status(
            delivery_execution_id=execution.id,
            new_status="OUT_FOR_DELIVERY",
            changed_by="system",
        )

        execution_repo.create_confirmation(
            delivery_execution_id=execution.id,
            received_by="Customer",
        )

        print("Seed data inserted successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    run()