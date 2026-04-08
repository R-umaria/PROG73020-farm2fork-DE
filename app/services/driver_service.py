from app.core.database import SessionLocal
from app.repositories.driver_repository import DriverRepository
from app.repositories.planning_repository import PlanningRepository


class DriverService:
    def __init__(self):
        self.db = SessionLocal()
        self.driver_repo = DriverRepository()
        self.planning_repo = PlanningRepository(self.db)

    def list_drivers(self):
        return self.driver_repo.list_all()

    def get_schedule(self, driver_id: int):
        assignments = self.planning_repo.get_driver_schedule(driver_id)

        stops = []

        for assignment in assignments:
            route_group = assignment.route_group
            if not route_group:
                continue

            for stop in sorted(route_group.stops, key=lambda s: s.sequence):
                delivery_request = stop.delivery_request
                customer = delivery_request.customer_details if delivery_request else None

                address = None
                customer_name = None

                if customer:
                    address = ", ".join(
                        filter(
                            None,
                            [
                                customer.street,
                                customer.city,
                                customer.province,
                                customer.postal_code,
                                customer.country,
                            ],
                        )
                    )
                    customer_name = customer.customer_name

                stops.append(
                    {
                        "route_group_id": str(route_group.id),
                        "route_name": route_group.name,
                        "scheduled_date": route_group.scheduled_date.isoformat()
                        if route_group.scheduled_date
                        else None,
                        "route_stop_id": str(stop.id),
                        "sequence": stop.sequence,
                        "estimated_arrival": stop.estimated_arrival.isoformat()
                        if stop.estimated_arrival
                        else None,
                        "stop_status": stop.stop_status,
                        "delivery_request_id": str(delivery_request.id)
                        if delivery_request
                        else None,
                        "order_id": delivery_request.order_id if delivery_request else None,
                        "customer_name": customer_name,
                        "address": address,
                    }
                )

        return {
            "driver_id": driver_id,
            "total_stops": len(stops),
            "stops": stops,
        }

    def start_day(self, driver_id: int):
        return {"driver_id": driver_id, "message": "Driver day started"}

    def complete_stop(self, route_stop_id: int):
        return {"route_stop_id": route_stop_id, "message": "Stop marked complete"}