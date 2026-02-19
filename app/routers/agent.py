import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent_log import AgentLog
from app.models.shipment import Shipment
from app.models.invoice import Invoice
from app.services.invoice_generator import generate_invoice
from app.services.payment_tracker import check_overdue, send_all_reminders
from app.services.ai_agent import ai_check_anomalies

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/generate-batch")
def generate_batch(db: Session = Depends(get_db)):
    """Batch generate invoices for uninvoiced shipments."""
    # Find shipments without invoices
    invoiced_shipment_ids = [r[0] for r in db.query(Invoice.shipment_id).all() if r[0]]
    query = db.query(Shipment)
    if invoiced_shipment_ids:
        query = query.filter(~Shipment.id.in_(invoiced_shipment_ids))
    unbilled = query.all()

    generated = []
    errors = []
    for shipment in unbilled:
        try:
            inv = generate_invoice(db, shipment.id)
            generated.append({"invoice_number": inv.invoice_number, "total": inv.total_amount})
        except Exception as e:
            errors.append({"shipment_id": shipment.id, "booking": shipment.booking_number, "error": str(e)})

    # Log agent action
    log = AgentLog(
        action="generate_batch",
        input_data=json.dumps({"unbilled_count": len(unbilled)}),
        output_data=json.dumps({"generated": len(generated), "errors": len(errors)}),
    )
    db.add(log)
    db.commit()

    return {"count": len(generated), "generated": generated, "errors": errors}


@router.post("/send-reminders")
def send_reminders(db: Session = Depends(get_db)):
    """Send payment reminders for overdue invoices."""
    # First mark overdue invoices
    overdue_count = check_overdue(db)
    # Then send reminders
    reminder_count = send_all_reminders(db)

    log = AgentLog(
        action="send_reminders",
        output_data=json.dumps({"newly_overdue": overdue_count, "reminders_sent": reminder_count}),
    )
    db.add(log)
    db.commit()

    return {"count": reminder_count, "newly_overdue": overdue_count}


@router.post("/check-anomalies")
def check_anomalies(db: Session = Depends(get_db)):
    """Check for anomalies in invoices and payments."""
    invoices = db.query(Invoice).filter(Invoice.status != "void").all()
    invoices_data = [
        {"id": inv.id, "invoice_number": inv.invoice_number, "total_amount": inv.total_amount,
         "shipment_id": inv.shipment_id, "status": inv.status}
        for inv in invoices
    ]
    anomalies = ai_check_anomalies(invoices_data)

    log = AgentLog(
        action="check_anomalies",
        input_data=json.dumps({"invoice_count": len(invoices_data)}),
        output_data=json.dumps({"anomalies": anomalies or []}),
    )
    db.add(log)
    db.commit()

    return {"anomalies": anomalies or [], "count": len(anomalies or [])}


@router.get("/logs")
def get_agent_logs(db: Session = Depends(get_db)):
    """Return recent agent logs."""
    logs = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "claude_prompt": log.claude_prompt,
            "claude_response": log.claude_response,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
