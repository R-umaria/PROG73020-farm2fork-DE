from app.models.assignment import Assignment

class AssignmentRepository:
    def __init__(self):
        self._assignments = [
            Assignment(id=1, delivery_id=1, driver_id=1, status="assigned"),
            Assignment(id=2, delivery_id=2, driver_id=2, status="active"),
        ]

    def list_all(self) -> list[Assignment]:
        return self._assignments
