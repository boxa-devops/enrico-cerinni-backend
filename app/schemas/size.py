from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SizeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class SizeCreate(SizeBase):
    pass


class SizeUpdate(SizeBase):
    name: Optional[str] = Field(None, min_length=1, max_length=50)


class SizeResponse(SizeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
