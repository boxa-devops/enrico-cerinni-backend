from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.sql import func
from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    expense_target_id = Column(Integer, nullable=True)
    expense_target_type = Column(String, nullable=True)
    
    date = Column(DateTime, nullable=False)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


