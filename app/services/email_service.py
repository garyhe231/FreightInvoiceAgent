from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.client import Client
from app.models.shipment import Shipment
from app.models.email_log import EmailLog
from app.models.port import Port
from app.config import settings


def draft_invoice_email(invoice: Invoice, client: Client, shipment: Shipment) -> dict:
    """Draft a professional invoice email for a freight shipment.

    Returns a dict with 'subject' and 'body' keys.
    """
    # Load port names for the route description
    subject = f"Invoice {invoice.invoice_number} \u2014 {settings.COMPANY_NAME}"

    body = (
        f"Dear {client.contact_name or client.company_name},\n"
        f"\n"
        f"Please find below the invoice details for your recent shipment.\n"
        f"\n"
        f"--- Invoice Details ---\n"
        f"Invoice Number : {invoice.invoice_number}\n"
        f"Issue Date     : {invoice.issue_date}\n"
        f"Due Date       : {invoice.due_date}\n"
        f"\n"
        f"--- Shipment Reference ---\n"
        f"Booking Number : {shipment.booking_number}\n"
        f"BL Number      : {shipment.bl_number or 'N/A'}\n"
        f"Vessel / Voyage: {shipment.vessel_name or 'N/A'} / {shipment.voyage_number or 'N/A'}\n"
        f"Container Type : {shipment.container_type}\n"
        f"\n"
        f"--- Amount ---\n"
        f"Total Amount   : ${invoice.total_amount:,.2f} USD\n"
        f"Amount Paid    : ${invoice.amount_paid:,.2f} USD\n"
        f"Balance Due    : ${invoice.balance_due:,.2f} USD\n"
        f"\n"
        f"Payment is due by {invoice.due_date}.\n"
        f"\n"
        f"--- Payment Instructions ---\n"
        f"Wire Transfer to:\n"
        f"  {settings.COMPANY_NAME}\n"
        f"  Bank of America\n"
        f"  Account: XXXX-XXXX-1234\n"
        f"  Routing: 026009593\n"
        f"  Reference: {invoice.invoice_number}\n"
        f"\n"
        f"If you have any questions regarding this invoice, please do not hesitate to\n"
        f"contact us at {settings.COMPANY_EMAIL} or {settings.COMPANY_PHONE}.\n"
        f"\n"
        f"Thank you for your business.\n"
        f"\n"
        f"Best regards,\n"
        f"Billing Department\n"
        f"{settings.COMPANY_NAME}\n"
        f"{settings.COMPANY_ADDRESS}\n"
    )

    return {"subject": subject, "body": body}


def draft_reminder_email(
    invoice: Invoice, client: Client, days_overdue: int
) -> dict:
    """Draft a professional but firm payment reminder email.

    Returns a dict with 'subject' and 'body' keys.
    """
    subject = (
        f"Payment Reminder: Invoice {invoice.invoice_number} "
        f"\u2014 {days_overdue} Days Overdue"
    )

    body = (
        f"Dear {client.contact_name or client.company_name},\n"
        f"\n"
        f"We are writing to remind you that payment for the following invoice is now\n"
        f"{days_overdue} days past due.\n"
        f"\n"
        f"--- Invoice Details ---\n"
        f"Invoice Number : {invoice.invoice_number}\n"
        f"Issue Date     : {invoice.issue_date}\n"
        f"Due Date       : {invoice.due_date}\n"
        f"Total Amount   : ${invoice.total_amount:,.2f} USD\n"
        f"Amount Paid    : ${invoice.amount_paid:,.2f} USD\n"
        f"Balance Due    : ${invoice.balance_due:,.2f} USD\n"
        f"\n"
        f"We kindly request that you arrange payment at your earliest convenience.\n"
        f"If payment has already been sent, please disregard this notice and provide\n"
        f"the transaction reference so we can update our records.\n"
        f"\n"
        f"--- Payment Instructions ---\n"
        f"Wire Transfer to:\n"
        f"  {settings.COMPANY_NAME}\n"
        f"  Bank of America\n"
        f"  Account: XXXX-XXXX-1234\n"
        f"  Routing: 026009593\n"
        f"  Reference: {invoice.invoice_number}\n"
        f"\n"
        f"For any questions, please contact us at {settings.COMPANY_EMAIL} or\n"
        f"{settings.COMPANY_PHONE}.\n"
        f"\n"
        f"Thank you for your prompt attention to this matter.\n"
        f"\n"
        f"Best regards,\n"
        f"Accounts Receivable\n"
        f"{settings.COMPANY_NAME}\n"
        f"{settings.COMPANY_ADDRESS}\n"
    )

    return {"subject": subject, "body": body}


def send_invoice(db: Session, invoice_id: int) -> EmailLog:
    """Send an invoice email (simulated) and update invoice status.

    Raises ValueError if the invoice is not found.
    Returns the created EmailLog record.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise ValueError(f"Invoice with id {invoice_id} not found")

    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if client is None:
        raise ValueError(f"Client for invoice {invoice_id} not found")

    shipment = db.query(Shipment).filter(Shipment.id == invoice.shipment_id).first()
    if shipment is None:
        raise ValueError(f"Shipment for invoice {invoice_id} not found")

    # Draft the email
    email_content = draft_invoice_email(invoice, client, shipment)

    # Create email log record
    email_log = EmailLog(
        invoice_id=invoice.id,
        recipient_email=client.email,
        subject=email_content["subject"],
        body=email_content["body"],
        email_type="invoice",
        status="simulated",
    )
    db.add(email_log)

    # Update invoice status
    invoice.status = "sent"
    invoice.sent_at = datetime.utcnow()

    db.commit()
    db.refresh(email_log)
    return email_log


def send_reminder(db: Session, invoice_id: int) -> EmailLog:
    """Send a payment reminder email (simulated) for an overdue invoice.

    Raises ValueError if the invoice is not found.
    Returns the created EmailLog record.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        raise ValueError(f"Invoice with id {invoice_id} not found")

    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if client is None:
        raise ValueError(f"Client for invoice {invoice_id} not found")

    # Calculate days overdue
    from datetime import date as date_type

    today = date_type.today()
    days_overdue = (today - invoice.due_date).days if invoice.due_date else 0
    if days_overdue < 0:
        days_overdue = 0

    # Draft the reminder
    email_content = draft_reminder_email(invoice, client, days_overdue)

    # Create email log record
    email_log = EmailLog(
        invoice_id=invoice.id,
        recipient_email=client.email,
        subject=email_content["subject"],
        body=email_content["body"],
        email_type="reminder",
        status="simulated",
    )
    db.add(email_log)

    db.commit()
    db.refresh(email_log)
    return email_log
