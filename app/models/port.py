from sqlalchemy import Column, Integer, String

from app.database import Base


class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    port_code = Column(String(10), unique=True, nullable=False)
    port_name = Column(String(100), nullable=False)
    country = Column(String(100))
    region = Column(String(50))  # "Asia", "Europe", "Americas"
