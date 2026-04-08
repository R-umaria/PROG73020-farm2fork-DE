from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.core.delivery_events import delivery_event_type_for_status
from app.core.delivery_status import (
    DeliveryExecutionStatus,
    normalize_delivery_execution_status,
    validate_delivery_execution_transition,
)
from app.models.db_models import (
    DeliveryConfirmation,
    DeliveryException,
    DeliveryExecution,
    DeliveryRequest,
    PickupRecord,
    RouteGroup,
    RouteStop,
    StatusHistory,
)
from app.repositories.event_repository import EventRepository


class ExecutionRepository:
    """Persistence boundary for delivery execution state and status history."""

    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)

    def create_execution(
        self,
        *,
        delivery_request_id: UUID,
        current_status: str | DeliveryExecutionStatus,
    ) -> DeliveryExecution:
        """Create the execution aggregate and emit the matching scheduled event."""

        canonical_status = normalize_delivery_execution_status(current_status)
        execution = DeliveryExecution(
            delivery_request_id=delivery_request_id,
            current_status=canonical_status.value,
        )
        self.db.add(execution)
        self.db.flush()

        history = StatusHistory(
            delivery_execution_id=execution.id,
            old_status=None,
            new_status=canonical_status.value,
            changed_by="system",
            reason="Initial execution record created",
        )
        self.db.add(history)
        self.db.flush()

        self._record_status_event(
            execution=execution,
            target_status=canonical_status,
            old_status=None,
            changed_by="system",
            reason=history.reason,
        )

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_status(
        self,
        *,
        delivery_execution_id: UUID,
        new_status: str | DeliveryExecutionStatus,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> DeliveryExecution | None:
        """Apply a canonical status transition and persist matching event metadata."""

        execution = (
            self.db.query(DeliveryExecution)
            .filter(DeliveryExecution.id == delivery_execution_id)
            .first()
        )
        if not execution:
            return None

        current_status, target_status = validate_delivery_execution_transition(
            execution.current_status,
            new_status,
        )

        execution.current_status = target_status.value
        self._apply_status_timestamps(execution, target_status)

        history = StatusHistory(
            delivery_execution_id=execution.id,
            old_status=current_status.value,
            new_status=target_status.value,
            changed_by=changed_by,
            reason=reason,
        )
        self.db.add(history)
        self.db.flush()

        self._record_status_event(
            execution=execution,
            target_status=target_status,
            old_status=current_status,
            changed_by=changed_by,
            reason=reason,
        )

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_by_delivery_request_id(self, delivery_request_id: UUID) -> DeliveryExecution | None:
        return (
            self.db.query(DeliveryExecution)
            .filter(DeliveryExecution.delivery_request_id == delivery_request_id)
            .first()
        )

    def get_tracking_context_by_order_id(self, order_id: int) -> DeliveryRequest | None:
        """Load the tracking read model context for a single order."""

        return (
            self.db.query(DeliveryRequest)
            .options(
                selectinload(DeliveryRequest.execution).selectinload(DeliveryExecution.status_history),
                selectinload(DeliveryRequest.route_stops)
                .selectinload(RouteStop.route_group)
                .selectinload(RouteGroup.driver_assignments),
            )
            .filter(DeliveryRequest.order_id == order_id)
            .first()
        )

    def log_exception(
        self,
        *,
        delivery_execution_id: UUID,
        exception_type: str,
        description: str,
        retry_allowed: bool,
    ) -> DeliveryException:
        exception = DeliveryException(
            delivery_execution_id=delivery_execution_id,
            exception_type=exception_type,
            description=description,
            retry_allowed=retry_allowed,
        )
        self.db.add(exception)
        self.db.commit()
        self.db.refresh(exception)
        return exception

    def create_confirmation(
        self,
        *,
        delivery_execution_id: UUID,
        received_by: str,
        proof_of_delivery_url: str | None = None,
        signature_data: str | None = None,
    ) -> DeliveryConfirmation:
        confirmation = DeliveryConfirmation(
            delivery_execution_id=delivery_execution_id,
            received_by=received_by,
            proof_of_delivery_url=proof_of_delivery_url,
            signature_data=signature_data,
        )
        self.db.add(confirmation)
        self.db.commit()
        self.db.refresh(confirmation)
        return confirmation

    def create_pickup_record(
        self,
        *,
        delivery_execution_id: UUID,
        location: str | None = None,
        collected_by: str | None = None,
    ) -> PickupRecord:
        pickup_record = PickupRecord(
            delivery_execution_id=delivery_execution_id,
            location=location,
            collected_by=collected_by,
        )
        self.db.add(pickup_record)
        self.db.commit()
        self.db.refresh(pickup_record)
        return pickup_record

    @staticmethod
    def _apply_status_timestamps(
        execution: DeliveryExecution,
        target_status: DeliveryExecutionStatus,
    ) -> None:
        """Maintain execution timestamps that mirror the canonical state model."""

        now = datetime.now(timezone.utc)

        if target_status == DeliveryExecutionStatus.OUT_FOR_DELIVERY:
            execution.started_at = execution.started_at or now
            execution.dispatched_at = execution.dispatched_at or now
            execution.out_for_delivery_at = execution.out_for_delivery_at or now
        elif target_status == DeliveryExecutionStatus.DELIVERED:
            execution.completed_at = execution.completed_at or now
        elif target_status == DeliveryExecutionStatus.FAILED:
            execution.failed_at = execution.failed_at or now

    def _record_status_event(
        self,
        *,
        execution: DeliveryExecution,
        target_status: DeliveryExecutionStatus,
        old_status: DeliveryExecutionStatus | None,
        changed_by: str | None,
        reason: str | None,
    ) -> None:
        """Persist an internal event record for every explicit status change."""

        delivery_request = self._load_delivery_request_context(execution.delivery_request_id)
        route_stop = self._select_route_stop(delivery_request)
        route_group = route_stop.route_group if route_stop is not None else None
        assignment = self._select_active_assignment(route_group.driver_assignments if route_group is not None else [])

        event_payload = {
            "event_version": "v1",
            "order_id": delivery_request.order_id,
            "delivery_request_id": str(delivery_request.id),
            "delivery_execution_id": str(execution.id),
            "delivery_status": target_status.value,
            "previous_status": old_status.value if old_status is not None else None,
            "changed_by": changed_by,
            "reason": reason,
            "route_group_id": str(route_group.id) if route_group is not None else None,
            "route_group_status": route_group.status if route_group is not None else None,
            "route_stop_id": str(route_stop.id) if route_stop is not None else None,
            "stop_sequence": route_stop.sequence if route_stop is not None else None,
            "stop_status": route_stop.stop_status if route_stop is not None else None,
            "estimated_arrival": self._format_event_datetime(route_stop.estimated_arrival) if route_stop is not None else None,
            "driver_id": assignment.driver_id if assignment is not None else None,
            "assignment_status": assignment.assignment_status if assignment is not None else None,
        }

        self.event_repo.record_event(
            aggregate_type="delivery_execution",
            aggregate_id=execution.id,
            order_id=delivery_request.order_id,
            event_type=delivery_event_type_for_status(target_status).value,
            event_payload=event_payload,
        )

    def _load_delivery_request_context(self, delivery_request_id: UUID) -> DeliveryRequest:
        return (
            self.db.query(DeliveryRequest)
            .options(
                selectinload(DeliveryRequest.route_stops)
                .selectinload(RouteStop.route_group)
                .selectinload(RouteGroup.driver_assignments),
            )
            .filter(DeliveryRequest.id == delivery_request_id)
            .one()
        )

    @staticmethod
    def _select_route_stop(delivery_request: DeliveryRequest) -> RouteStop | None:
        if not delivery_request.route_stops:
            return None
        return sorted(
            delivery_request.route_stops,
            key=lambda stop: (stop.sequence, str(stop.id)),
        )[0]

    @staticmethod

    @staticmethod
    def _format_event_datetime(value) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")

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
            key=lambda assignment: (
                assignment.assigned_at,
                assignment.driver_id,
                str(assignment.id),
            ),
        )[0]
