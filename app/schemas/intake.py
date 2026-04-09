from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeliveryItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_item_id: int
    item_name: str
    quantity: int = Field(gt=0)


class DeliveryRequestCreate(BaseModel):
    model_config = ConfigDict(title="DeliveryRequestCreateV1")

    order_id: int
    customer_id: int
    request_timestamp: datetime
    items: list[DeliveryItemCreate] = Field(default_factory=list)

    @field_validator("request_timestamp")
    @classmethod
    def validate_request_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("request_timestamp must include a timezone offset")
        return value.astimezone(UTC)


class IntakeResponse(BaseModel):
    model_config = ConfigDict(title="DeliveryRequestAcceptedResponseV1")

    message: str
    order_id: int
    request_status: Literal["received"]
    delivery_request_id: UUID | None = None


class CustomerSyncResponse(BaseModel):
    model_config = ConfigDict(title="CustomerSyncResponseV1")

    message: str
    delivery_request_id: UUID
    sync_status: Literal["completed"]
