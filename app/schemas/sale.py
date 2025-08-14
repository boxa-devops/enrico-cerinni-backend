from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.models.sale import PaymentMethod, SaleStatus


class SaleItemBase(BaseModel):
    product_variant_id: int
    quantity: int
    unit_price: Decimal


class SaleItemCreate(SaleItemBase):
    pass


class SaleItemResponse(SaleItemBase):
    id: int
    total_price: Decimal
    product_variant_sku: str
    product_name: str
    color_name: str
    size_name: str
    created_at: str

    class Config:
        from_attributes = True


class SaleBase(BaseModel):
    client_id: Optional[int] = None
    total_amount: Decimal
    paid_amount: Decimal = 0
    payment_method: PaymentMethod
    notes: Optional[str] = None
    items: List[SaleItemCreate]


class SaleCreate(SaleBase):
    pass


class SaleUpdate(BaseModel):
    client_id: Optional[int] = None
    total_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    payment_method: Optional[PaymentMethod] = None
    status: Optional[SaleStatus] = None
    notes: Optional[str] = None


class SaleResponse(SaleBase):
    id: int
    receipt_number: str
    status: SaleStatus
    created_at: str
    updated_at: Optional[str] = None
    items: List[SaleItemResponse]
    client_name: Optional[str] = None

    class Config:
        from_attributes = True


class SaleFilter(BaseModel):
    client_id: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    status: Optional[SaleStatus] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    size: int = 10


class PaginatedSaleResponse(BaseModel):
    items: List[SaleResponse]
    pagination: dict


class DebtPaymentRequest(BaseModel):
    client_id: int
    payment_amount: Decimal
