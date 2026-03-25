from fastapi import APIRouter
from app.api.routes import health, deliveries, drivers, assignments, pages

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(deliveries.router, prefix="/deliveries", tags=["Deliveries"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["Drivers"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])

# UI pages are served without /api prefix by mounting separately in main import path
page_router = APIRouter()
page_router.include_router(pages.router)
