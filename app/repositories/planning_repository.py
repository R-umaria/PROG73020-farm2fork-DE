from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.db_models import (
    DeliveryRequest,
    DriverAssignment,
    RouteGroup,
    RouteStop,
)


class PlanningRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_backlog_requests(self) -> list[DeliveryRequest]:
        return (
            self.db.query(DeliveryRequest)
            .options(
                selectinload(DeliveryRequest.customer_details),
                selectinload(DeliveryRequest.request_snapshot),
                selectinload(DeliveryRequest.route_stops),
            )
            .order_by(DeliveryRequest.request_timestamp.asc(), DeliveryRequest.order_id.asc())
            .all()
        )

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
            .options(
                selectinload(RouteGroup.stops),
                selectinload(RouteGroup.driver_assignments),
            )
            .filter(RouteGroup.id == route_group_id)
            .first()
        )

    def list_route_groups(self) -> list[RouteGroup]:
        return (
            self.db.query(RouteGroup)
            .options(
                selectinload(RouteGroup.stops),
                selectinload(RouteGroup.driver_assignments),
            )
            .order_by(RouteGroup.scheduled_date.asc(), RouteGroup.name.asc())
            .all()
        )

    def get_active_driver_loads(self) -> dict[int, int]:
        rows: Iterable[tuple[int, int]] = (
            self.db.query(
                DriverAssignment.driver_id,
                func.count(DriverAssignment.id),
            )
            .join(RouteGroup, RouteGroup.id == DriverAssignment.route_group_id)
            .filter(DriverAssignment.assignment_status.in_(["assigned", "accepted"]))
            .filter(RouteGroup.status.in_(["draft", "scheduled", "in_progress"]))
            .group_by(DriverAssignment.driver_id)
            .all()
        )
        return {driver_id: load_count for driver_id, load_count in rows}
