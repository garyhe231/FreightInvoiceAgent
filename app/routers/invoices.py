from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.client import Client
from app.models.shipment import Shipment
from app.models.port import Port
from app.schemas.invoice import InvoiceResponse, InvoiceDetail, InvoiceLineResponse
from app.services.invoice_generator import generate_invoice as gen_invoice
from app.services.email_service import send_invoice as svc_send_invoice
from app.services.pdf_generator import generate_pdf

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by invoice status"),
    db: Session = Depends(get_db),
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    invoices = query.order_by(Invoice.created_at.desc()).all()

    results = []
    for inv in invoices:
        data = InvoiceResponse.model_validate(inv)
        if inv.client_id:
            client = db.query(Client).filter(Client.id == inv.client_id).first()
            if client:
                data.client_name = client.company_name
        results.append(data)
    return results


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get line items
    lines = (
        db.query(InvoiceLine)
        .filter(InvoiceLine.invoice_id == invoice_id)
        .order_by(InvoiceLine.line_order)
        .all()
    )

    # Get client name
    client_name = None
    if invoice.client_id:
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        if client:
            client_name = client.company_name

    # Get shipment booking number
    booking_number = None
    if invoice.shipment_id:
        shipment = db.query(Shipment).filter(Shipment.id == invoice.shipment_id).first()
        if shipment:
            booking_number = shipment.booking_number

    data = InvoiceDetail.model_validate(invoice)
    data.client_name = client_name
    data.booking_number = booking_number
    data.lines = [InvoiceLineResponse.model_validate(line) for line in lines]
    return data


@router.post("/generate/{shipment_id}")
def generate_invoice(shipment_id: int, db: Session = Depends(get_db)):
    """Generate an invoice for a shipment. Calls invoice_generator service."""
    try:
        invoice = gen_invoice(db, shipment_id)
        return {"message": "Invoice generated", "invoice_id": invoice.id, "invoice_number": invoice.invoice_number, "total_amount": invoice.total_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invoice_id}/send")
def send_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Send an invoice via email."""
    try:
        email_log = svc_send_invoice(db, invoice_id)
        return {"message": "Invoice sent", "email_id": email_log.id, "recipient": email_log.recipient_email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Set invoice status to void."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = "void"
    db.commit()
    db.refresh(invoice)

    data = InvoiceResponse.model_validate(invoice)
    if invoice.client_id:
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        if client:
            data.client_name = client.company_name
    return data


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    """Download invoice PDF."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    lines = db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice_id).order_by(InvoiceLine.line_order).all()
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    shipment = db.query(Shipment).filter(Shipment.id == invoice.shipment_id).first()
    origin_port = db.query(Port).filter(Port.id == shipment.origin_port_id).first() if shipment else None
    dest_port = db.query(Port).filter(Port.id == shipment.destination_port_id).first() if shipment else None

    try:
        pdf_path = generate_pdf(invoice, lines, client, shipment, origin_port, dest_port)
        invoice.pdf_path = pdf_path
        db.commit()
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{invoice.invoice_number}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
