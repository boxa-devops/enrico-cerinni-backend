from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    phone = Column(String(20), index=True, nullable=True)
    telegram_chat_id = Column(String(64), index=True, nullable=True)
    address = Column(Text, nullable=True)
    
    debt_amount = Column(Numeric(10, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
