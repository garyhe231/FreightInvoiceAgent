from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(50), nullable=False)
    input_data = Column(String(5000))
    output_data = Column(String(5000))
    claude_prompt = Column(String(5000))
    claude_response = Column(String(5000))
    created_at = Column(DateTime, server_default=func.now())
