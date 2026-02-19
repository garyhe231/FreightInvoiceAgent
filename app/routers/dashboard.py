from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.client import Client
from app.schemas.dashboard import DashboardSummary, AgingResponse, RevenueMonthly, ActivityItem

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    today = date.today()
    first_of_month = today.replace(day=1)

    # Total AR: sum of balance_due where status in (sent, partial, overdue)
    total_ar = (
        db.query(func.coalesce(func.sum(Invoice.balance_due), 0))
        .filter(Invoice.status.in_(["sent", "partial", "overdue"]))
        .scalar()
    )

    # Invoices created this month
    invoices_this_month = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.issue_date >= first_of_month)
        .scalar()
    )

    # Overdue count
    overdue_count = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == "overdue")
        .scalar()
    )

    # Revenue MTD: sum of amount_paid on payments this month
    revenue_mtd = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.payment_date >= first_of_month)
        .scalar()
    )

    return DashboardSummary(
        total_ar=float(total_ar),
        invoices_this_month=int(invoices_this_month),
        overdue_count=int(overdue_count),
        revenue_mtd=float(revenue_mtd),
    )


@router.get("/aging", response_model=AgingResponse)
def dashboard_aging(db: Session = Depends(get_db)):
    today = date.today()

    # Get all open invoices (sent, partial, overdue)
    invoices = (
        db.query(Invoice)
        .filter(Invoice.status.in_(["sent", "partial", "overdue"]))
        .all()
    )

    bucket_0_30 = 0.0
    bucket_31_60 = 0.0
    bucket_61_90 = 0.0
    bucket_90_plus = 0.0

    for inv in invoices:
        if inv.issue_date is None:
            continue
        days_old = (today - inv.issue_date).days
        if days_old <= 30:
            bucket_0_30 += inv.balance_due or 0
        elif days_old <= 60:
            bucket_31_60 += inv.balance_due or 0
        elif days_old <= 90:
            bucket_61_90 += inv.balance_due or 0
        else:
            bucket_90_plus += inv.balance_due or 0

    return AgingResponse(
        bucket_0_30=bucket_0_30,
        bucket_31_60=bucket_31_60,
        bucket_61_90=bucket_61_90,
        bucket_90_plus=bucket_90_plus,
    )


@router.get("/revenue-monthly", response_model=RevenueMonthly)
def dashboard_revenue_monthly(db: Session = Depends(get_db)):
    today = date.today()
    months = []
    amounts = []

    for i in range(5, -1, -1):
        month_start = (today - relativedelta(months=i)).replace(day=1)
        if i > 0:
            month_end = (today - relativedelta(months=i - 1)).replace(day=1) - timedelta(days=1)
        else:
            # Current month: end is today
            month_end = today

        total = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.payment_date >= month_start)
            .filter(Payment.payment_date <= month_end)
            .scalar()
        )

        months.append(month_start.strftime("%b %Y"))
        amounts.append(float(total))

    return RevenueMonthly(months=months, amounts=amounts)


@router.get("/recent-activity", response_model=list[ActivityItem])
def dashboard_recent_activity(db: Session = Depends(get_db)):
    activities: list[ActivityItem] = []

    # Recent invoices
    recent_invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(20).all()
    for inv in recent_invoices:
        client_name = None
        if inv.client_id:
            client = db.query(Client).filter(Client.id == inv.client_id).first()
            if client:
                client_name = client.company_name
        activities.append(
            ActivityItem(
                date=inv.created_at.strftime("%Y-%m-%d %H:%M") if inv.created_at else "",
                event=f"Invoice {inv.status}",
                invoice_number=inv.invoice_number,
                client_name=client_name,
                amount=inv.total_amount,
            )
        )

    # Recent payments
    recent_payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(20).all()
    for pmt in recent_payments:
        invoice = db.query(Invoice).filter(Invoice.id == pmt.invoice_id).first()
        invoice_number = invoice.invoice_number if invoice else None
        client_name = None
        if invoice and invoice.client_id:
            client = db.query(Client).filter(Client.id == invoice.client_id).first()
            if client:
                client_name = client.company_name
        activities.append(
            ActivityItem(
                date=pmt.created_at.strftime("%Y-%m-%d %H:%M") if pmt.created_at else "",
                event="Payment received",
                invoice_number=invoice_number,
                client_name=client_name,
                amount=pmt.amount,
            )
        )

    # Sort by date desc, take top 20
    activities.sort(key=lambda x: x.date, reverse=True)
    return activities[:20]
