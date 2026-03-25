from app.repositories.assignment_repository import AssignmentRepository

class AssignmentService:
    def __init__(self):
        self.repo = AssignmentRepository()

    def list_assignments(self):
        return self.repo.list_all()
