from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class SalaryPaymentBase(BaseModel):
    employee_id: int
    amount: Decimal
    payment_date: datetime
    notes: Optional[str] = None


class SalaryPaymentCreate(SalaryPaymentBase):
    pass


class SalaryPaymentUpdate(BaseModel):
    employee_id: Optional[int] = None
    amount: Optional[Decimal] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None


class SalaryPaymentResponse(SalaryPaymentBase):
    id: int
    employee_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
