from uuid import UUID
from app.models import execution
from app.repositories.execution_repository import ExecutionRepository
from app.core.database import SessionLocal

class DeliveryActionsService:
    def __init__(self):
        self.db = SessionLocal()
        self.repo = ExecutionRepository(self.db)

    def start_delivery(self, delivery_execution_id: UUID):
        return self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status="Out for Delivery",
            changed_by="driver",
            reason="Driver started route",
        )

    def complete_delivery(self, delivery_execution_id: UUID, received_by: str, proof_url: str | None = None):
        self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status="Delivered",
            changed_by="driver",
            reason="Stop completed successfully",
        )
        return self.repo.create_confirmation(
            delivery_execution_id=delivery_execution_id,
            received_by=received_by,
            proof_of_delivery_url=proof_url,
        )

    def fail_delivery(self, delivery_execution_id: UUID, exception_type: str, description: str, retry_allowed: bool):
        self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status="Failed",
            changed_by="driver",
            reason=description,
        )
        return self.repo.log_exception(
            delivery_execution_id=delivery_execution_id,
            exception_type=exception_type,
            description=description,
            retry_allowed=retry_allowed,
        )
    def complete_pickup(
        self,
        delivery_execution_id: UUID,
        location: str | None = None,
        collected_by: str | None = None,
    ):
        execution = self.repo.update_status(
            delivery_execution_id=delivery_execution_id,
            new_status="Picked Up",
            changed_by="pickup_desk",
            reason="Pickup completed",
        )
        if not execution:
            return None

        return self.repo.create_pickup_record(
            delivery_execution_id=delivery_execution_id,
            location=location,
            collected_by=collected_by,
        )