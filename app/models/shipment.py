from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_number = Column(String(50), unique=True, nullable=False)
    shipper_id = Column(Integer, ForeignKey("clients.id"))
    consignee_id = Column(Integer, ForeignKey("clients.id"))
    origin_port_id = Column(Integer, ForeignKey("ports.id"))
    destination_port_id = Column(Integer, ForeignKey("ports.id"))
    container_type = Column(String(10), nullable=False)  # "20GP", "40GP", "40HC", "LCL"
    container_count = Column(Integer, default=1)
    cbm = Column(Float)  # for LCL
    weight_kg = Column(Float)
    commodity_description = Column(String(200))
    vessel_name = Column(String(100))
    voyage_number = Column(String(50))
    etd = Column(Date)
    eta = Column(Date)
    bl_number = Column(String(50))
    status = Column(String(20), default="booked")  # booked, shipped, arrived, delivered
    bill_to = Column(String(20), default="shipper")  # "shipper" or "consignee"
    created_at = Column(DateTime, server_default=func.now())
