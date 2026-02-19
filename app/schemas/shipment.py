from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ShipmentBase(BaseModel):
    booking_number: str
    shipper_id: Optional[int] = None
    consignee_id: Optional[int] = None
    origin_port_id: Optional[int] = None
    destination_port_id: Optional[int] = None
    container_type: str  # "20GP", "40GP", "40HC", "LCL"
    container_count: Optional[int] = 1
    cbm: Optional[float] = None
    weight_kg: Optional[float] = None
    commodity_description: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    etd: Optional[date] = None
    eta: Optional[date] = None
    bl_number: Optional[str] = None
    status: Optional[str] = "booked"
    bill_to: Optional[str] = "shipper"


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentResponse(ShipmentBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShipmentDetail(ShipmentResponse):
    origin_port_name: Optional[str] = None
    destination_port_name: Optional[str] = None
    shipper_name: Optional[str] = None
    consignee_name: Optional[str] = None
    has_invoice: bool = False
