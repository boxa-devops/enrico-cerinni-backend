from pydantic import BaseModel, Field
from typing import Optional


class SeasonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class SeasonResponse(SeasonBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
