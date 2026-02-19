from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey

from app.database import Base


class RateCard(Base):
    __tablename__ = "rate_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_port_id = Column(Integer, ForeignKey("ports.id"))
    destination_port_id = Column(Integer, ForeignKey("ports.id"))
    container_type = Column(String(10), nullable=False)  # "20GP", "40GP", "40HC", "LCL"
    base_ocean_freight = Column(Float, nullable=False)  # USD per container or per CBM
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    carrier_name = Column(String(100))
    is_active = Column(Boolean, default=True)
