from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router, page_router

# NEW
# from app.api.health import router as health_router

#the path above was wrong? ^^
from app.api.routes.health import router as health_router

app = FastAPI(title="Farm2Fork Delivery Execution Service")

# UI pages
app.include_router(page_router)

# API routes
app.include_router(api_router, prefix="/api")

# Health + version routes (REQUIRED)
app.include_router(health_router)

# Static assets
app.mount("/static", StaticFiles(directory="driver_ui/static"), name="static")