from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services import email_service


def record_payment(
    db: Session,
    invoice_id: int,
    amount: float,
    payment_date: date,
    payment_method: str,
    reference_number: str,
    notes: str = "",
) -> Payment:
    """Record a payment against an invoice and update invoice balances.

    Raises ValueError if the invoice is not found.
    Returns the created Payment record.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise ValueError(f"Invoice with id {invoice_id} not found")

    # Create payment record
    payment = Payment(
        invoice_id=invoice_id,
        payment_date=payment_date,
        amount=amount,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes,
    )
    db.add(payment)

    # Update invoice totals
    invoice.amount_paid = (invoice.amount_paid or 0) + amount
    invoice.balance_due = invoice.total_amount - invoice.amount_paid

    # Update invoice status based on balance
    if invoice.balance_due <= 0:
        invoice.balance_due = 0.0
        invoice.status = "paid"
    elif invoice.amount_paid > 0:
        invoice.status = "partial"

    db.commit()
    db.refresh(payment)
    return payment


def check_overdue(db: Session) -> int:
    """Find all sent invoices that are past due and mark them as overdue.

    Returns the number of invoices updated.
    """
    today = date.today()

    overdue_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.status == "sent",
            Invoice.due_date < today,
        )
        .all()
    )

    count = 0
    for invoice in overdue_invoices:
        invoice.status = "overdue"
        count += 1

    if count > 0:
        db.commit()

    return count


def send_all_reminders(db: Session) -> int:
    """Send reminder emails for all overdue invoices.

    Returns the number of reminders sent.
    """
    overdue_invoices = (
        db.query(Invoice)
        .filter(Invoice.status == "overdue")
        .all()
    )

    count = 0
    for invoice in overdue_invoices:
        try:
            email_service.send_reminder(db, invoice.id)
            count += 1
        except ValueError as e:
            print(f"Failed to send reminder for invoice {invoice.id}: {e}")

    return count
