from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.intake import DeliveryItemCreate, DeliveryRequestCreate


class DeliveryCreate(DeliveryRequestCreate):
    model_config = ConfigDict(title="ManualDeliveryCreateV1")


class DeliveryResponse(DeliveryRequestCreate):
    model_config = ConfigDict(from_attributes=True, title="DeliveryResponseV1")

    id: UUID
    request_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
