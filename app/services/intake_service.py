from __future__ import annotations

from uuid import UUID

from app.schemas.intake import DeliveryRequestCreate


class IntakeService:
    def receive_delivery_request(self, payload: DeliveryRequestCreate):
        return {
            "message": "Delivery request accepted (v1); persistence not implemented in this intake path yet",
            "order_id": payload.order_id,
            "request_status": "received",
            "delivery_request_id": None,
        }

    def sync_customer_details(self, delivery_request_id: UUID):
        return {
            "message": "Customer details sync placeholder",
            "delivery_request_id": delivery_request_id,
            "sync_status": "placeholder",
        }
