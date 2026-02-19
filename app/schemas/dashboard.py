from typing import Optional

from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    total_ar: float
    invoices_this_month: int
    overdue_count: int
    revenue_mtd: float


class AgingResponse(BaseModel):
    bucket_0_30: float
    bucket_31_60: float
    bucket_61_90: float
    bucket_90_plus: float


class RevenueMonthly(BaseModel):
    months: list[str]
    amounts: list[float]


class ActivityItem(BaseModel):
    date: str
    event: str
    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    amount: Optional[float] = None
