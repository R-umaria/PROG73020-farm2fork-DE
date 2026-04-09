from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.intake import DeliveryItemCreate, DeliveryRequestCreate


class DeliveryCustomerDetailsResponse(BaseModel):
    """Customer enrichment exposed to the driver portal for a delivery request."""

    model_config = ConfigDict(from_attributes=True, title="DeliveryCustomerDetailsResponseV1")

    customer_name: str
    phone_number: str
    street: str
    city: str
    province: str
    postal_code: str
    country: str
    latitude: float | None = None
    longitude: float | None = None
    geocode_status: str | None = None


class DeliveryCreate(DeliveryRequestCreate):
    model_config = ConfigDict(title="ManualDeliveryCreateV1")


class DeliveryResponse(DeliveryRequestCreate):
    """Delivery request record returned by the v1 delivery endpoints."""

    model_config = ConfigDict(from_attributes=True, title="DeliveryResponseV1")

    id: UUID
    request_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    customer_details: DeliveryCustomerDetailsResponse | None = None
