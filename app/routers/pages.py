from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/invoices")
def invoices_page(request: Request):
    return templates.TemplateResponse("invoices/list.html", {"request": request})


@router.get("/invoices/{invoice_id}")
def invoice_detail_page(request: Request, invoice_id: int):
    return templates.TemplateResponse("invoices/detail.html", {"request": request, "invoice_id": invoice_id})


@router.get("/shipments")
def shipments_page(request: Request):
    return templates.TemplateResponse("shipments/list.html", {"request": request})


@router.get("/shipments/{shipment_id}")
def shipment_detail_page(request: Request, shipment_id: int):
    return templates.TemplateResponse("shipments/detail.html", {"request": request, "shipment_id": shipment_id})


@router.get("/clients")
def clients_page(request: Request):
    return templates.TemplateResponse("clients/list.html", {"request": request})


@router.get("/clients/{client_id}")
def client_detail_page(request: Request, client_id: int):
    return templates.TemplateResponse("clients/detail.html", {"request": request, "client_id": client_id})


@router.get("/payments")
def payments_page(request: Request):
    return templates.TemplateResponse("payments/list.html", {"request": request})


@router.get("/agent")
def agent_page(request: Request):
    return templates.TemplateResponse("agent/console.html", {"request": request})
