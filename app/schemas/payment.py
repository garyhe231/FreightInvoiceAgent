from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    invoice_id: int
    payment_date: date
    amount: float
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    payment_date: date
    amount: float
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    invoice_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
