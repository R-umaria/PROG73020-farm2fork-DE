import logging
import subprocess

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.services.demo_seed_service import seed_demo_data_if_enabled

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.allow_all_frontend_origins else settings.frontend_allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


def apply_database_migrations() -> None:
    logger.info("Applying database migrations during app startup")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup_prepare_database_and_seed_demo_data():
    try:
        apply_database_migrations()
        seed_demo_data_if_enabled()
    except Exception:
        logger.exception("Database preparation or demo data seeding failed during startup")
        raise
