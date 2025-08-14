from pydantic import BaseModel
from typing import List, Dict, Any
from decimal import Decimal


class DashboardStats(BaseModel):
    total_products: int
    total_clients: int
    total_sales: int
    total_revenue: Decimal
    low_stock_products: int
    recent_sales: List[Dict[str, Any]]
    monthly_revenue: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]


class RecentTransaction(BaseModel):
    id: int
    type: str
    amount: Decimal
    description: str
    created_at: str


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_transactions: List[RecentTransaction]
