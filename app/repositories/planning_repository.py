from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.db_models import (
    DriverAssignment,
    RouteGroup,
    RouteStop,
    DeliveryRequest,
    CustomerDetails,
)


class PlanningRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_route_group(
        self,
        *,
        name: str,
        scheduled_date,
        status: str,
        zone_code: str,
        total_stops: int = 0,
        estimated_distance_km=None,
        estimated_duration_min=None,
    ) -> RouteGroup:
        route_group = RouteGroup(
            name=name,
            scheduled_date=scheduled_date,
            status=status,
            zone_code=zone_code,
            total_stops=total_stops,
            estimated_distance_km=estimated_distance_km,
            estimated_duration_min=estimated_duration_min,
        )
        self.db.add(route_group)
        self.db.commit()
        self.db.refresh(route_group)
        return route_group

    def add_route_stop(
        self,
        *,
        route_group_id: UUID,
        delivery_request_id: UUID,
        sequence: int,
        estimated_arrival=None,
        stop_status: str,
    ) -> RouteStop:
        stop = RouteStop(
            route_group_id=route_group_id,
            delivery_request_id=delivery_request_id,
            sequence=sequence,
            estimated_arrival=estimated_arrival,
            stop_status=stop_status,
        )
        self.db.add(stop)
        self.db.commit()
        self.db.refresh(stop)
        return stop

    def assign_driver(
        self,
        *,
        route_group_id: UUID,
        driver_id: int,
        assignment_status: str,
    ) -> DriverAssignment:
        assignment = DriverAssignment(
            route_group_id=route_group_id,
            driver_id=driver_id,
            assignment_status=assignment_status,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_route_group_by_id(self, route_group_id: UUID) -> RouteGroup | None:
        return (
            self.db.query(RouteGroup)
            .filter(RouteGroup.id == route_group_id)
            .first()
        )
    def get_driver_schedule(self, driver_id: int):
        assignments = (
            self.db.query(DriverAssignment)
            .options(
                joinedload(DriverAssignment.route_group)
                .joinedload(RouteGroup.stops)
                .joinedload(RouteStop.delivery_request)
                .joinedload(DeliveryRequest.customer_details)
            )
            .filter(DriverAssignment.driver_id == driver_id)
            .all()
        )

        return assignments

    
    
