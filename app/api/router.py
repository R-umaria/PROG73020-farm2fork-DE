from fastapi import APIRouter
from app.api.routes import health, intake, planning, tracking, driver, pages

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(intake.router, prefix="/delivery-requests", tags=["Intake"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning"])
api_router.include_router(tracking.router, prefix="/delivery-status", tags=["Tracking"])
api_router.include_router(driver.router, prefix="/driver", tags=["Driver"])

page_router = APIRouter()
page_router.include_router(pages.router)
