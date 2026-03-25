from fastapi import APIRouter
from app.schemas.assignment import AssignmentResponse
from app.services.assignment_service import AssignmentService

router = APIRouter()
service = AssignmentService()

@router.get("/", response_model=list[AssignmentResponse])
def list_assignments():
    return service.list_assignments()
