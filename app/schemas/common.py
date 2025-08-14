from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class ResponseModel(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None


class PaginationModel(BaseModel):
    page: int
    size: int
    total: int
    pages: int


class PaginatedResponse(BaseModel):
    items: List[Any]
    pagination: PaginationModel


class BaseModelWithTimestamps(BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
