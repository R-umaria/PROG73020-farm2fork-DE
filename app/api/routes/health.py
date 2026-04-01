from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine

router = APIRouter()

@router.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return {"status": "error", "db": "disconnected"}


@router.get("/version")
def version():
    return {"version": "1.0.0"}