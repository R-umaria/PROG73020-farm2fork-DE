from uuid import UUID

from app.core.database import SessionLocal
from app.core.delivery_status import DeliveryExecutionStatus
from app.repositories.execution_repository import ExecutionRepository


class DeliveryActionsService:
    def __init__(self):
        self.db = SessionLocal()
        self.repo = ExecutionRepository(self.db)

    def start_delivery(self, delivery_execution_id: UUID):
        return self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status=DeliveryExecutionStatus.OUT_FOR_DELIVERY,
            changed_by="driver",
            reason="Driver started route",
        )

    def complete_delivery(
        self,
        delivery_execution_id: UUID,
        received_by: str,
        proof_url: str | None = None,
    ):
        execution = self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status=DeliveryExecutionStatus.DELIVERED,
            changed_by="driver",
            reason="Stop completed successfully",
        )
        if not execution:
            return None

        return self.repo.create_confirmation(
            delivery_execution_id=delivery_execution_id,
            received_by=received_by,
            proof_of_delivery_url=proof_url,
        )

    def fail_delivery(
        self,
        delivery_execution_id: UUID,
        exception_type: str,
        description: str,
        retry_allowed: bool,
    ):
        execution = self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status=DeliveryExecutionStatus.FAILED,
            changed_by="driver",
            reason=description,
        )
        if not execution:
            return None

        return self.repo.log_exception(
            delivery_execution_id=delivery_execution_id,
            exception_type=exception_type,
            description=description,
            retry_allowed=retry_allowed,
        )
