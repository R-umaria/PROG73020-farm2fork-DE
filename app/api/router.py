from fastapi import APIRouter

from app.api.routes import (
    assignments,
    deliveries,
    delivery_actions,
    driver,
    drivers,
    health,
    intake,
    pages,
    planning,
    tracking,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(intake.router, prefix="/delivery-requests", tags=["Intake"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning"])
api_router.include_router(tracking.router, prefix="/delivery-status", tags=["Tracking"])
api_router.include_router(driver.router, prefix="/driver", tags=["Driver"])
api_router.include_router(deliveries.router, prefix="/deliveries", tags=["Deliveries"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["Drivers"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(delivery_actions.router, tags=["Delivery Actions"])

page_router = APIRouter()
page_router.include_router(pages.router)
