class TrackingService:
    def get_status(self, order_id: str):
        return {"order_id": order_id, "delivery_status": "scheduled"}
