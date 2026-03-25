from app.repositories.driver_repository import DriverRepository

class DriverService:
    def __init__(self):
        self.repo = DriverRepository()

    def list_drivers(self):
        return self.repo.list_all()
