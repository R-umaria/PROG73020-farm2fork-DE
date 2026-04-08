from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.delivery_status import DeliveryExecutionStatus


class DeliveryStatusResponse(BaseModel):
    model_config = ConfigDict(title="DeliveryStatusResponseV1")

    order_id: int
    delivery_status: DeliveryExecutionStatus
    delivery_execution_id: UUID | None = None
