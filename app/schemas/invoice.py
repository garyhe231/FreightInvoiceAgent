from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InvoiceLineResponse(BaseModel):
    id: int
    invoice_id: int
    line_order: int
    charge_code: str
    description: str
    quantity: float
    unit_price: float
    line_total: float

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    shipment_id: Optional[int] = None
    client_id: Optional[int] = None
    issue_date: date
    due_date: date
    subtotal: float
    tax_amount: Optional[float] = 0
    total_amount: float
    amount_paid: Optional[float] = 0
    balance_due: float
    status: Optional[str] = "draft"
    notes: Optional[str] = None
    pdf_path: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceDetail(InvoiceResponse):
    lines: list[InvoiceLineResponse] = []
    booking_number: Optional[str] = None
