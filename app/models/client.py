from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=False)
    client_type = Column(String(20), nullable=False)  # "shipper" or "consignee"
    contact_name = Column(String(100))
    email = Column(String(200), nullable=False)
    phone = Column(String(50))
    address = Column(String(500))
    city = Column(String(100))
    country = Column(String(100))
    payment_terms_days = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
