from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


class DeliveryItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore", populate_by_name=True)

    external_item_id: int = Field(validation_alias=AliasChoices("external_item_id", "externalItemId", "id"))
    item_name: str = Field(validation_alias=AliasChoices("item_name", "itemName", "name"))
    quantity: int = Field(gt=0)


class DeliveryRequestCreate(BaseModel):
    model_config = ConfigDict(title="DeliveryRequestCreateV1", extra="ignore", populate_by_name=True)

    order_id: int = Field(validation_alias=AliasChoices("order_id", "orderId"))
    customer_id: int = Field(validation_alias=AliasChoices("customer_id", "customerID", "customerId"))
    request_timestamp: datetime = Field(validation_alias=AliasChoices("request_timestamp", "requestTimestamp", "timestamp"))
    items: list[DeliveryItemCreate] = Field(default_factory=list)
    order_type: Literal["delivery", "pickup"] = "delivery"
    pickup: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_order_type(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        order_type = data.get("order_type", data.get("orderType"))
        pickup = data.get("pickup")

        normalized_order_type: str | None = None
        if isinstance(order_type, str) and order_type.strip():
            candidate = order_type.strip().lower()
            if candidate in {"pickup", "delivery"}:
                normalized_order_type = candidate
        elif isinstance(pickup, bool):
            normalized_order_type = "pickup" if pickup else "delivery"

        if normalized_order_type is None:
            normalized_order_type = "delivery"

        normalized = dict(data)
        normalized["order_type"] = normalized_order_type
        normalized["pickup"] = normalized_order_type == "pickup"
        return normalized

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
    order_type: Literal["delivery", "pickup"] = "delivery"
    auto_sync_status: str | None = None
    auto_schedule_status: str | None = None


class CustomerSyncResponse(BaseModel):
    model_config = ConfigDict(title="CustomerSyncResponseV1")

    message: str
    delivery_request_id: UUID
    sync_status: Literal["completed"]
