from fastapi import APIRouter

from app.api.routes import (
    assignments,
    deliveries,
    delivery_actions,
    dev,
    driver,
    driver_auth,
    drivers,
    health,
    intake,
    # pages,
    planning,
    shifts,
    tracking,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(intake.router, prefix="/delivery-requests", tags=["Intake"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning"])
api_router.include_router(tracking.router, prefix="/delivery-status", tags=["Tracking"])
api_router.include_router(driver.router, prefix="/driver", tags=["Driver"])
api_router.include_router(driver_auth.router, prefix="/driver-auth", tags=["Driver Auth"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["Shifts"])
api_router.include_router(deliveries.router, prefix="/deliveries", tags=["Deliveries"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["Drivers"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(delivery_actions.router, tags=["Delivery Actions"])

# page_router = APIRouter()
# page_router.include_router(pages.router)

api_router.include_router(dev.router, prefix="/dev", tags=["Dev"])
