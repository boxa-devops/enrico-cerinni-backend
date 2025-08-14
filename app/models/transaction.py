from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
    Enum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TransactionType(str, enum.Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    EXPENSE = "expense"
    REFUND = "refund"
    DEBT_PAYMENT = "debt_payment"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sale = relationship("Sale")
    client = relationship("Client")
