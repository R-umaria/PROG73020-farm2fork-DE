from app.schemas.intake import DeliveryRequestCreate

class IntakeService:
    def receive_delivery_request(self, payload: DeliveryRequestCreate):
        return {
            "message": "Delivery request received and snapshot saved",
            "order_id": payload.order_id,
        }

    def sync_customer_details(self, delivery_request_id: int):
        return {
            "message": "Customer details sync placeholder",
            "delivery_request_id": delivery_request_id,
        }
