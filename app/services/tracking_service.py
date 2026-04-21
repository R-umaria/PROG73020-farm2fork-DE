"""DB-backed delivery tracking read model service."""

from __future__ import annotations

from datetime import timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.delivery_status import normalize_delivery_execution_status
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.tracking import DeliveryStatusHistoryEntry, DeliveryStatusResponse


_STATUS_ORDER = {
    "scheduled": 0,
    "out_for_delivery": 1,
    "delivered": 2,
    "failed": 3,
}


class TrackingService:
    """Projects the persisted execution aggregate into the tracking contract."""

    def __init__(self, db: Session | None = None):
        self.db: Session = db or SessionLocal()
        self.repo = ExecutionRepository(self.db)

    def get_status(self, order_id: int) -> DeliveryStatusResponse | None:
        """Return the persisted tracking view for an order, if one exists."""

        # Route modules keep service instances alive, so expire the current session
        # before building the read model to avoid stale execution/status data.
        self.db.expire_all()
        delivery_request = self.repo.get_tracking_context_by_order_id(order_id)
        if delivery_request is None or delivery_request.execution is None:
            return None

        execution = delivery_request.execution
        status_history = sorted(
            execution.status_history,
            key=lambda history: (history.changed_at, _STATUS_ORDER.get(str(history.new_status), 99)),
        )
        latest_history = status_history[-1] if status_history else None

        route_stop = self._select_route_stop(delivery_request.route_stops)
        route_group = route_stop.route_group if route_stop is not None else None
        assignment = self._select_active_assignment(route_group.driver_assignments if route_group is not None else [])

        return DeliveryStatusResponse(
            order_id=delivery_request.order_id,
            customer_id=delivery_request.customer_id,
            delivery_request_id=delivery_request.id,
            delivery_execution_id=execution.id,
            delivery_status=normalize_delivery_execution_status(execution.current_status),
            latest_status_at=self._ensure_utc(latest_history.changed_at) if latest_history is not None else None,
            latest_status_reason=latest_history.reason if latest_history is not None else None,
            route_group_id=route_group.id if route_group is not None else None,
            route_group_status=route_group.status if route_group is not None else None,
            route_stop_id=route_stop.id if route_stop is not None else None,
            stop_sequence=route_stop.sequence if route_stop is not None else None,
            stop_status=route_stop.stop_status if route_stop is not None else None,
            estimated_arrival=self._ensure_utc(route_stop.estimated_arrival) if route_stop is not None else None,
            scheduled_for=self._ensure_utc(route_stop.estimated_arrival) if route_stop and route_stop.estimated_arrival else None,
            assigned_driver_id=assignment.driver_id if assignment is not None else None,
            assignment_status=assignment.assignment_status if assignment is not None else None,
            dispatched_at=self._ensure_utc(execution.dispatched_at),
            out_for_delivery_at=self._ensure_utc(execution.out_for_delivery_at),
            completed_at=self._ensure_utc(execution.completed_at),
            failed_at=self._ensure_utc(execution.failed_at),
            status_history=[
                DeliveryStatusHistoryEntry(
                    status=normalize_delivery_execution_status(history.new_status),
                    changed_at=self._ensure_utc(history.changed_at),
                    changed_by=history.changed_by,
                    reason=history.reason,
                )
                for history in status_history
            ],
        )

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _ensure_utc(value):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _select_route_stop(route_stops) -> object | None:
        if not route_stops:
            return None
        return sorted(route_stops, key=lambda stop: (stop.sequence, str(stop.id)))[0]

    @staticmethod
    def _select_active_assignment(assignments) -> object | None:
        active_assignments = [
            assignment
            for assignment in assignments
            if assignment.assignment_status in {"assigned", "accepted"}
        ]
        if not active_assignments:
            return None
        return sorted(
            active_assignments,
            key=lambda assignment: (assignment.assigned_at, assignment.driver_id, str(assignment.id)),
        )[0]
