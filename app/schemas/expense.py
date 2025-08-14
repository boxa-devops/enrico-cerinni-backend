from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class ExpenseBase(BaseModel):
    description: str
    amount: Decimal
    category: str
    date: datetime
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
