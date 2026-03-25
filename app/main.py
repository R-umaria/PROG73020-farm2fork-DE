from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router, page_router

app = FastAPI(title="Farm2Fork Delivery Execution Service")

# UI pages
app.include_router(page_router)

# API routes
app.include_router(api_router, prefix="/api")

# Static assets
app.mount("/static", StaticFiles(directory="driver_ui/static"), name="static")
