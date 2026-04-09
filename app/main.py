from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router, page_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

# Allow the separate Next.js driver portal to call the API directly during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(page_router)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="driver_ui/static"), name="static")
