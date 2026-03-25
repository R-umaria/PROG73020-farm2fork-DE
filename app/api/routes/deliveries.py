from fastapi import APIRouter, HTTPException
from app.schemas.delivery import DeliveryCreate, DeliveryResponse
from app.services.delivery_service import DeliveryService

router = APIRouter()
service = DeliveryService()

@router.get("/", response_model=list[DeliveryResponse])
def list_deliveries():
    return service.list_deliveries()

@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: int):
    delivery = service.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

@router.post("/", response_model=DeliveryResponse, status_code=201)
def create_delivery(payload: DeliveryCreate):
    return service.create_delivery(payload)
