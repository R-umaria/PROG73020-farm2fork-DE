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
                selectinload(RouteGroup.stops)
                .selectinload(RouteStop.delivery_request)
                .selectinload(DeliveryRequest.customer_details),
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

    def list_driver_route_stops(self, driver_id: int) -> list[RouteStop]:
        return (
            self.db.query(RouteStop)
            .join(RouteGroup, RouteGroup.id == RouteStop.route_group_id)
            .join(DriverAssignment, DriverAssignment.route_group_id == RouteGroup.id)
            .options(
                selectinload(RouteStop.route_group),
                selectinload(RouteStop.delivery_request).selectinload(DeliveryRequest.customer_details),
            )
            .filter(DriverAssignment.driver_id == driver_id)
            .filter(DriverAssignment.assignment_status.in_(["assigned", "accepted"]))
            .filter(RouteGroup.status.in_(["draft", "scheduled", "in_progress"]))
            .order_by(RouteGroup.scheduled_date.asc(), RouteStop.sequence.asc(), RouteStop.id.asc())
            .all()
        )

    def update_route_stop_status(self, *, route_stop_id: UUID, stop_status: str) -> RouteStop | None:
        stop = (
            self.db.query(RouteStop)
            .options(
                selectinload(RouteStop.route_group),
                selectinload(RouteStop.delivery_request).selectinload(DeliveryRequest.customer_details),
            )
            .filter(RouteStop.id == route_stop_id)
            .first()
        )
        if stop is None:
            return None

        stop.stop_status = stop_status
        self.db.commit()
        self.db.refresh(stop)
        return stop

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

    def update_route_group_routing(self,*,route_group_id: UUID,estimated_distance_km: float,estimated_duration_min: int, route_payload:dict | None = None,) -> RouteGroup | None:
        group = self.db.query(RouteGroup).filter(RouteGroup.id == route_group_id).first()
        if group is None:
            return None
        group.estimated_distance_km = estimated_distance_km
        group.estimated_duration_min = estimated_duration_min
        group.route_payload = route_payload
        self.db.commit()
        self.db.refresh(group)
        return group

    def update_route_stop_eta(self,*,route_stop_id: UUID,estimated_arrival,) -> RouteStop | None:
        stop = self.db.query(RouteStop).filter(RouteStop.id == route_stop_id).first()
        if stop is None:
            return None
        stop.estimated_arrival = estimated_arrival
        self.db.commit()
        self.db.refresh(stop)
        return stop