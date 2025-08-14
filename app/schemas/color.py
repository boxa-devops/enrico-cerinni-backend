from pydantic import BaseModel, Field
from typing import Optional


class ColorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hex_code: Optional[str] = Field(None, max_length=7)
    description: Optional[str] = None


class ColorCreate(ColorBase):
    pass


class ColorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hex_code: Optional[str] = Field(None, max_length=7)
    description: Optional[str] = None


class ColorResponse(ColorBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
