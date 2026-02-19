from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class EmailLog(Base):
    __tablename__ = "email_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    recipient_email = Column(String(200), nullable=False)
    subject = Column(String(300), nullable=False)
    body = Column(String(5000), nullable=False)
    email_type = Column(String(20), nullable=False)  # "invoice", "reminder", "receipt"
    status = Column(String(20), default="simulated")  # "simulated", "sent", "failed"
    sent_at = Column(DateTime, server_default=func.now())
