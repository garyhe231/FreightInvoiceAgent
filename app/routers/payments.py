from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(tags=["payments"])


@router.get("/api/payments", response_model=list[PaymentResponse])
def list_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
    results = []
    for pmt in payments:
        data = PaymentResponse.model_validate(pmt)
        invoice = db.query(Invoice).filter(Invoice.id == pmt.invoice_id).first()
        if invoice:
            data.invoice_number = invoice.invoice_number
        results.append(data)
    return results


@router.post("/api/payments", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    # Validate invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == payload.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Create payment
    payment = Payment(**payload.model_dump())
    db.add(payment)

    # Update invoice amounts
    invoice.amount_paid = (invoice.amount_paid or 0) + payload.amount
    invoice.balance_due = invoice.total_amount - invoice.amount_paid

    # Update invoice status
    if invoice.balance_due <= 0:
        invoice.balance_due = 0
        invoice.status = "paid"
    else:
        invoice.status = "partial"

    db.commit()
    db.refresh(payment)

    data = PaymentResponse.model_validate(payment)
    data.invoice_number = invoice.invoice_number
    return data


@router.get("/api/invoices/{invoice_id}/payments", response_model=list[PaymentResponse])
def list_payments_for_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    payments = (
        db.query(Payment)
        .filter(Payment.invoice_id == invoice_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )
    results = []
    for pmt in payments:
        data = PaymentResponse.model_validate(pmt)
        data.invoice_number = invoice.invoice_number
        results.append(data)
    return results
