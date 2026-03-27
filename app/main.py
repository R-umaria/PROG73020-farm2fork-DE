from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router, page_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.include_router(page_router)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="driver_ui/static"), name="static")
