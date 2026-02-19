from sqlalchemy import Column, Integer, String, Float, ForeignKey

from app.database import Base


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    line_order = Column(Integer, nullable=False)
    charge_code = Column(String(20), nullable=False)
    description = Column(String(200), nullable=False)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
