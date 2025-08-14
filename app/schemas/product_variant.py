from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ProductVariantBase(BaseModel):
    product_id: int
    color_id: int
    size_id: int
    sku: str = Field(..., min_length=1, max_length=50)
    price: Decimal = Field(..., ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: int = Field(0, ge=0)
    min_stock_level: int = Field(0, ge=0)


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    color_id: Optional[int] = None
    size_id: Optional[int] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    color_name: Optional[str] = None
    size_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductVariantBulkCreate(BaseModel):
    product_id: int
    variants: List[ProductVariantCreate]


class ProductVariantBulkUpdate(BaseModel):
    variants: List[dict]  # List of variant updates with id and new values
