from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.db_models import (
    DeliveryItem,
    DeliveryRequest,
    DeliveryRequestSnapshot,
)


class DeliveryRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_delivery_request(
        self,
        *,
        order_id: int,
        customer_id: int,
        request_timestamp,
        request_status: str,
        raw_payload: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> DeliveryRequest:
        delivery_request = DeliveryRequest(
            order_id=order_id,
            customer_id=customer_id,
            request_timestamp=request_timestamp,
            request_status=request_status,
        )
        self.db.add(delivery_request)
        self.db.flush()

        snapshot = DeliveryRequestSnapshot(
            delivery_request_id=delivery_request.id,
            request_payload=raw_payload,
        )
        self.db.add(snapshot)

        for item in items:
            delivery_item = DeliveryItem(
                delivery_request_id=delivery_request.id,
                external_item_id=item["external_item_id"],
                item_name=item["item_name"],
                quantity=item["quantity"],
            )
            self.db.add(delivery_item)

        self.db.commit()
        self.db.refresh(delivery_request)
        return delivery_request

    def get_by_id(self, delivery_request_id: UUID) -> DeliveryRequest | None:
        return (
            self.db.query(DeliveryRequest)
            .options(
                selectinload(DeliveryRequest.items),
                selectinload(DeliveryRequest.customer_details),
            )
            .filter(DeliveryRequest.id == delivery_request_id)
            .first()
        )

    def get_by_order_id(self, order_id: int) -> DeliveryRequest | None:
        return (
            self.db.query(DeliveryRequest)
            .options(
                selectinload(DeliveryRequest.items),
                selectinload(DeliveryRequest.request_snapshot),
            )
            .filter(DeliveryRequest.order_id == order_id)
            .first()
        )

    def list_all(self) -> list[DeliveryRequest]:
        return (
            self.db.query(DeliveryRequest)
            .options(selectinload(DeliveryRequest.items), selectinload(DeliveryRequest.customer_details))
            .all()
        )
