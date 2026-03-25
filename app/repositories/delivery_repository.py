from app.models.delivery import Delivery

class DeliveryRepository:
    def __init__(self):
        self._deliveries = [
            Delivery(
                id=1,
                order_id="ORD-1001",
                customer_name="Alex Johnson",
                address="100 Queen St W, Toronto",
                status="scheduled",
                latitude=43.6532,
                longitude=-79.3832,
            ),
            Delivery(
                id=2,
                order_id="ORD-1002",
                customer_name="Priya Shah",
                address="200 King St E, Toronto",
                status="out_for_delivery",
                latitude=43.6519,
                longitude=-79.3686,
            ),
        ]

    def list_all(self) -> list[Delivery]:
        return self._deliveries

    def get_by_id(self, delivery_id: int) -> Delivery | None:
        return next((d for d in self._deliveries if d.id == delivery_id), None)

    def create(self, delivery: Delivery) -> Delivery:
        self._deliveries.append(delivery)
        return delivery
