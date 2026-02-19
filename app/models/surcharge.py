from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey

from app.database import Base


class Surcharge(Base):
    __tablename__ = "surcharges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    charge_code = Column(String(20), nullable=False)
    charge_name = Column(String(100), nullable=False)
    calculation_type = Column(String(20), nullable=False)  # "fixed", "per_container", "percentage", "per_cbm"
    amount = Column(Float, nullable=False)
    percentage_of = Column(String(20))  # "ocean_freight" if calculation_type=percentage
    applies_to = Column(String(20), default="all")  # "FCL", "LCL", or "all"
    origin_port_id = Column(Integer, ForeignKey("ports.id"), nullable=True)
    destination_port_id = Column(Integer, ForeignKey("ports.id"), nullable=True)
    is_active = Column(Boolean, default=True)
