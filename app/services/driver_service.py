class DriverService:
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
    def list_drivers(self):
        return self.repo.list_all()