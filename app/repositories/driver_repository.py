from app.core.config import settings
from app.models.driver import Driver


class DriverRepository:
    def __init__(self):
        self._drivers = [
            Driver(
                id=index,
                name=f"Driver {index:03d}",
                vehicle_type="Cargo Van" if index % 5 else "Box Truck",
                status="available",
            )
            for index in range(1, settings.planning_daily_route_capacity + 1)
        ]

    def list_all(self) -> list[Driver]:
        return self._drivers
