from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))  # wire_transfer, check, ach
    reference_number = Column(String(100))
    notes = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
