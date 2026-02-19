from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(20), unique=True, nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0)
    balance_due = Column(Float, nullable=False)
    status = Column(String(20), default="draft")  # draft, sent, partial, paid, overdue, void
    notes = Column(String(1000))
    pdf_path = Column(String(500))
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
