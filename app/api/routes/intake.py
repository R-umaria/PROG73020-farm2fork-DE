from fastapi import APIRouter
from app.schemas.intake import DeliveryRequestCreate, IntakeResponse
from app.services.intake_service import IntakeService

router = APIRouter()
service = IntakeService()

@router.post("/", response_model=IntakeResponse, status_code=201)
def create_delivery_request(payload: DeliveryRequestCreate):
    return service.receive_delivery_request(payload)

@router.post("/{delivery_request_id}/customer-sync")
def sync_customer_details(delivery_request_id: int):
    return service.sync_customer_details(delivery_request_id)
