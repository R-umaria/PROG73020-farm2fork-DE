from fastapi import APIRouter
from app.services.demo_seed_service import DemoSeedService

router = APIRouter()
service = DemoSeedService()

@router.post('/seed-demo')
def seed_demo():
    return service.seed()
