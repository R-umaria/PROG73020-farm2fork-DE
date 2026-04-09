from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.integrations.customer_module_client import CustomerModuleClient
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamServiceError,
    UpstreamTimeoutError,
)
from app.integrations.geocoding_client import GeocodingClient
from app.repositories.customer_repository import CustomerRepository
from app.repositories.delivery_request_repository import DeliveryRequestRepository
from app.schemas.intake import CustomerSyncResponse, DeliveryRequestCreate, IntakeResponse


class IntakeConflictError(ValueError):
    """Raised when the same order_id is submitted with a conflicting payload."""


class DeliveryRequestNotFoundError(ValueError):
    """Raised when a delivery request cannot be found for customer sync."""


class IntakeService:
    def __init__(
        self,
        db: Session | None = None,
        *,
        customer_client: CustomerModuleClient | None = None,
        geocoding_client: GeocodingClient | None = None,
    ):
        self.db: Session = db or SessionLocal()
        self.repo = DeliveryRequestRepository(self.db)
        self.customer_repo = CustomerRepository(self.db)
        self.customer_client = customer_client or CustomerModuleClient()
        self.geocoding_client = geocoding_client or GeocodingClient()

    def receive_delivery_request(self, payload: DeliveryRequestCreate) -> IntakeResponse:
        raw_payload = payload.model_dump(mode="json")
        existing = self.repo.get_by_order_id(payload.order_id)

        if existing is not None:
            existing_payload = self._canonicalize_existing_request(existing)
            incoming_payload = self._canonicalize_payload(raw_payload)

            if existing_payload != incoming_payload:
                raise IntakeConflictError(
                    f"Conflicting delivery request already exists for order_id {payload.order_id}"
                )

            return IntakeResponse(
                message="Delivery request already received (v1)",
                order_id=existing.order_id,
                request_status="received",
                delivery_request_id=existing.id,
            )

        delivery_request = self.repo.create_delivery_request(
            order_id=payload.order_id,
            customer_id=payload.customer_id,
            request_timestamp=payload.request_timestamp,
            request_status="received",
            raw_payload=raw_payload,
            items=[item.model_dump() for item in payload.items],
        )

        return IntakeResponse(
            message="Delivery request persisted (v1)",
            order_id=delivery_request.order_id,
            request_status="received",
            delivery_request_id=delivery_request.id,
        )

    def sync_customer_details(self, delivery_request_id: UUID) -> CustomerSyncResponse:
        delivery_request = self.repo.get_by_id(delivery_request_id)
        if delivery_request is None:
            raise DeliveryRequestNotFoundError(
                f"Delivery request {delivery_request_id} was not found"
            )

        customer = self.customer_client.get_customer_details(delivery_request.customer_id)
        geocode = self.geocoding_client.geocode_address(
            street=customer.address.street,
            city=customer.address.city,
            province=customer.address.province,
            postal_code=customer.address.postal_code,
            country=customer.address.country,
        )

        self.customer_repo.save_customer_enrichment(
            delivery_request_id=delivery_request_id,
            raw_payload=customer.model_dump(mode="json"),
            customer_name=customer.customer_name,
            phone_number=customer.phone_number,
            street=customer.address.street,
            city=customer.address.city,
            province=customer.address.province,
            postal_code=customer.address.postal_code,
            country=customer.address.country,
            latitude=geocode.latitude,
            longitude=geocode.longitude,
            geocode_status="resolved",
        )

        return CustomerSyncResponse(
            message="Customer details synced (v1)",
            delivery_request_id=delivery_request_id,
            sync_status="completed",
        )

    def close(self) -> None:
        self.db.close()

    def _canonicalize_existing_request(self, existing) -> dict[str, Any]:
        if existing.request_snapshot is not None:
            return self._canonicalize_payload(existing.request_snapshot.request_payload)

        return self._canonicalize_payload(
            {
                "order_id": existing.order_id,
                "customer_id": existing.customer_id,
                "request_timestamp": existing.request_timestamp,
                "items": [
                    {
                        "external_item_id": item.external_item_id,
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                    }
                    for item in existing.items
                ],
            }
        )

    def _canonicalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        items = payload.get("items", [])
        canonical_items = sorted(
            [
                {
                    "external_item_id": int(item["external_item_id"]),
                    "item_name": str(item["item_name"]),
                    "quantity": int(item["quantity"]),
                }
                for item in items
            ],
            key=lambda item: (
                item["external_item_id"],
                item["item_name"],
                item["quantity"],
            ),
        )

        request_timestamp = payload.get("request_timestamp")
        if isinstance(request_timestamp, str):
            normalized_timestamp = request_timestamp.replace("Z", "+00:00")
            normalized_timestamp = (
                datetime.fromisoformat(normalized_timestamp)
                .astimezone(UTC)
                .isoformat()
                .replace("+00:00", "Z")
            )
        else:
            normalized_timestamp = request_timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")

        return {
            "order_id": int(payload["order_id"]),
            "customer_id": int(payload["customer_id"]),
            "request_timestamp": normalized_timestamp,
            "items": canonical_items,
        }
