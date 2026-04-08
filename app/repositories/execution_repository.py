from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.delivery_status import (
    DeliveryExecutionStatus,
    normalize_delivery_execution_status,
    validate_delivery_execution_transition,
)
from app.models.db_models import (
    DeliveryConfirmation,
    DeliveryException,
    DeliveryExecution,
    PickupRecord,
    StatusHistory,
)


class ExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_execution(
        self,
        *,
        delivery_request_id: UUID,
        current_status: str | DeliveryExecutionStatus,
    ) -> DeliveryExecution:
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

        self.db.commit()
        self.db.refresh(execution)
        return execution

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
        now = datetime.now(timezone.utc)

        if target_status == DeliveryExecutionStatus.OUT_FOR_DELIVERY:
            execution.started_at = execution.started_at or now
            execution.out_for_delivery_at = execution.out_for_delivery_at or now
        elif target_status == DeliveryExecutionStatus.DELIVERED:
            execution.completed_at = execution.completed_at or now
        elif target_status == DeliveryExecutionStatus.FAILED:
            execution.failed_at = execution.failed_at or now
