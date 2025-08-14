from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
    Enum,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class SaleStatus(str, enum.Enum):
    COMPLETED = "completed"
    PARTIALLY_PAID = "partially_paid"
    DEBT = "debt"
    CANCELLED = "cancelled"
    PENDING = "pending"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    
    receipt_number = Column(String(50), unique=True, index=True, nullable=False)
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(SaleStatus), default=SaleStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("Client", backref="sales")
    items = relationship("SaleItem", backref="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product_variant = relationship("ProductVariant")
