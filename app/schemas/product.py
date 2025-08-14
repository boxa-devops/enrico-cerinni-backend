from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal
from app.schemas.common import PaginationModel
from app.schemas.product_variant import ProductVariantResponse


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    season_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    sku: str = Field(..., min_length=1, max_length=50)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    season_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    sku: str
    created_at: str
    updated_at: Optional[str] = None
    brand_name: Optional[str] = None
    season_name: Optional[str] = None
    category_name: Optional[str] = None
    variants: Optional[List[ProductVariantResponse]] = None


class ProductFilter(BaseModel):
    name: Optional[str] = None
    brand_id: Optional[int] = None
    season_id: Optional[int] = None
    category_id: Optional[int] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


class PaginatedProductResponse(BaseModel):
    items: List[ProductResponse]
    pagination: PaginationModel
