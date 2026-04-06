from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

router = APIRouter()


@router.get("/health")
def health_check():
    response = {"status": "ok", "service": settings.app_name}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        response["db"] = "connected"
    except Exception:
        response["status"] = "error"
        response["db"] = "disconnected"
    return response


@router.get("/version")
def version():
    return {"service": settings.app_name, "version": settings.app_version}
