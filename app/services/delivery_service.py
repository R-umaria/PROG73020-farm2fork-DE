from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.delivery_request_repository import DeliveryRequestRepository
from app.schemas.delivery import DeliveryCreate


class DeliveryService:
    def __init__(self):
        self.db: Session = SessionLocal()
        self.repo = DeliveryRequestRepository(self.db)

    def list_deliveries(self):
        return self.repo.list_all()

    def get_delivery(self, delivery_id):
        return self.repo.get_by_id(delivery_id)

    def create_delivery(self, payload: DeliveryCreate):
        return self.repo.create_delivery_request(
            order_id=payload.order_id,
            customer_id=payload.customer_id,
            request_timestamp=payload.request_timestamp,
            request_status="received",
            raw_payload={
                "source": "manual_delivery_create_v1",
                **payload.model_dump(mode="json"),
            },
            items=[item.model_dump() for item in payload.items],
        )
