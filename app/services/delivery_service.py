from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.repositories.delivery_request_repository import DeliveryRequestRepository


class DeliveryService:
    def __init__(self):
        self.db: Session = SessionLocal()
        self.repo = DeliveryRequestRepository(self.db)

    def list_deliveries(self):
        return self.repo.list_all()

    def get_delivery(self, delivery_id):
        return self.repo.get_by_id(delivery_id)

    def create_delivery(self, payload):
        return self.repo.create_delivery_request(
            order_id=payload.order_id,
            customer_id=1,  # temp placeholder
            request_timestamp=payload.request_timestamp,
            request_status="RECEIVED",
            raw_payload={"source": "api"},
            items=[],
        )