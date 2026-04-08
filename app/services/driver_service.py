from app.repositories.driver_repository import DriverRepository

class DriverService:
    # MOCK IMPLEMENTATION - In a real application, this would interact with a database or external API
    def list_drivers(self):
        return [
            {
                "id": 1,
                "name": "Alex Carter",
                "vehicle_type": "Van",
                "status": "available",
            },
            {
                "id": 2,
                "name": "Priya Singh",
                "vehicle_type": "Truck",
                "status": "on_route",
            },
        ]

    def get_todays_schedule(self, driver_id: int):
        return {
            "driver_id": driver_id,
            "stops": [
                {"route_stop_id": 1, "address": "Placeholder Stop 1", "status": "scheduled"},
                {"route_stop_id": 2, "address": "Placeholder Stop 2", "status": "scheduled"},
            ],
        }

    def start_day(self, driver_id: int):
        return {"driver_id": driver_id, "message": "Driver day started"}

    def complete_stop(self, route_stop_id: int):
        return {"route_stop_id": route_stop_id, "message": "Stop marked complete"}