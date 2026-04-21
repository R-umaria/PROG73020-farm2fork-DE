from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.demo_seed_service import DemoSeedService

router = APIRouter()


@router.post('/seed-demo')
def seed_demo(db: Session = Depends(get_db)):
    service = DemoSeedService(db)
    try:
        return service.seed()
    finally:
        service.close()
