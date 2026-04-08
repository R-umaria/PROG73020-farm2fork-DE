from app.models.driver import Driver


class DriverRepository:
    def __init__(self):
        self._drivers = [
            Driver(id=1, name="Jordan Lee", vehicle_type="Van", status="available"),
            Driver(id=2, name="Sam Patel", vehicle_type="Bike", status="available"),
            Driver(id=3, name="Avery Chen", vehicle_type="Truck", status="on_route"),
        ]

    def list_all(self) -> list[Driver]:
        return self._drivers
