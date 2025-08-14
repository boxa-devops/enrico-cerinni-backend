from pydantic import BaseModel, Field
from typing import Optional


class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class BrandResponse(BrandBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
