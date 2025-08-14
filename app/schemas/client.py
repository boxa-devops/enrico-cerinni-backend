from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from decimal import Decimal
from app.schemas.common import PaginationModel


class ClientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    telegram_chat_id: Optional[str] = Field(None, max_length=64)
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    telegram_chat_id: Optional[str] = Field(None, max_length=64)
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    debt_amount: Decimal
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None


class ClientDebtUpdate(BaseModel):
    debt_amount: Decimal = Field(..., ge=0)


class ClientFilter(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    has_debt: Optional[bool] = None
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


class PaginatedClientResponse(BaseModel):
    items: List[ClientResponse]
    pagination: PaginationModel
