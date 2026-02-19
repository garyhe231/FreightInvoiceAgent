from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClientBase(BaseModel):
    company_name: str
    client_type: str  # "shipper" or "consignee"
    contact_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    payment_terms_days: Optional[int] = 30
    is_active: Optional[bool] = True


class ClientCreate(ClientBase):
    pass


class ClientResponse(ClientBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
