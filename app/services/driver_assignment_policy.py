from __future__ import annotations

from dataclasses import dataclass

from app.models.driver import Driver
from app.repositories.driver_repository import DriverRepository


@dataclass(frozen=True)
class DriverSelection:
    driver: Driver
    current_load: int


class DriverAssignmentPolicy:
    """Deterministic default driver-assignment policy.

    Current rule:
    - only drivers with status == "available" are eligible
    - prefer lower current load
    - break ties by driver id, then driver name
    """

    def __init__(self, driver_repository: DriverRepository | None = None):
        self.driver_repository = driver_repository or DriverRepository()

    def select_driver(self, current_loads: dict[int, int]) -> DriverSelection | None:
        eligible_drivers = [
            driver
            for driver in self.driver_repository.list_all()
            if driver.status.strip().lower() == "available"
        ]
        if not eligible_drivers:
            return None

        selected_driver = min(
            eligible_drivers,
            key=lambda driver: (
                current_loads.get(driver.id, 0),
                driver.id,
                driver.name,
            ),
        )
        return DriverSelection(
            driver=selected_driver,
            current_load=current_loads.get(selected_driver.id, 0),
        )
