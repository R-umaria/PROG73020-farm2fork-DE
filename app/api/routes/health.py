from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/version")
def version():
    return {"service": settings.app_name, "version": settings.app_version}
