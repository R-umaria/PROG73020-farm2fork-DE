from app.models.delivery import Delivery
from app.repositories.delivery_repository import DeliveryRepository
from app.schemas.delivery import DeliveryCreate

class DeliveryService:
    def __init__(self):
        self.repo = DeliveryRepository()

    def list_deliveries(self):
        return self.repo.list_all()

    def get_delivery(self, delivery_id: int):
        return self.repo.get_by_id(delivery_id)

    def create_delivery(self, payload: DeliveryCreate):
        next_id = len(self.repo.list_all()) + 1
        delivery = Delivery(
            id=next_id,
            order_id=payload.order_id,
            customer_name=payload.customer_name,
            address=payload.address,
            status="created",
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        return self.repo.create(delivery)
