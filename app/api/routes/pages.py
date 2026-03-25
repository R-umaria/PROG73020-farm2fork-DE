from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="driver_ui/templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/delivery/{delivery_id}", response_class=HTMLResponse)
def delivery_detail(request: Request, delivery_id: int):
    return templates.TemplateResponse(
        "delivery_detail.html",
        {"request": request, "delivery_id": delivery_id},
    )
