from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from datetime import datetime
from enum import Enum


class ReportTypeEnum(str, Enum):
    SALES = "sales"
    FINANCE = "finance"
    INVENTORY = "inventory"
    CLIENTS = "clients"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


class ReportFormatEnum(str, Enum):
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class DateRangeFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ReportFilters(BaseModel):
    date_range: Optional[DateRangeFilter] = None
    client_ids: Optional[List[int]] = None
    product_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None
    brand_ids: Optional[List[int]] = None
    payment_methods: Optional[List[str]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


# Base schemas for report requests and responses
class ReportRequestBase(BaseModel):
    report_type: ReportTypeEnum
    filters: Optional[ReportFilters] = None
    format: ReportFormatEnum = ReportFormatEnum.JSON


class ReportGenerateRequest(ReportRequestBase):
    name: Optional[str] = None
    description: Optional[str] = None
    save_report: bool = False


# Sales Report Schemas
class SalesMetric(BaseModel):
    total_revenue: Decimal
    total_sales: int
    avg_order_value: Decimal
    conversion_rate: float


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    variant_name: str
    sales_count: int
    total_revenue: Decimal


class SalesTrendPoint(BaseModel):
    date: datetime
    sales_count: int
    revenue: Decimal


class SalesReportData(BaseModel):
    metrics: SalesMetric
    top_products: List[TopProduct]
    sales_trend: List[SalesTrendPoint]
    sales_by_payment_method: Dict[str, Decimal]
    sales_by_category: Dict[str, Decimal]


# Finance Report Schemas
class FinanceMetric(BaseModel):
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    profit_margin: float
    cash_flow: Decimal


class ExpenseBreakdown(BaseModel):
    suppliers: Decimal
    salaries: Decimal
    rent: Decimal
    utilities: Decimal
    marketing: Decimal
    other: Decimal


class MonthlyFinanceData(BaseModel):
    month: str
    revenue: Decimal
    expenses: Decimal
    profit: Decimal


class PaymentMethodBreakdown(BaseModel):
    cash: Decimal
    card: Decimal
    transfer: Decimal
    debt: Decimal


class FinanceReportData(BaseModel):
    metrics: FinanceMetric
    expense_breakdown: ExpenseBreakdown
    monthly_data: List[MonthlyFinanceData]
    payment_methods: PaymentMethodBreakdown


# Inventory Report Schemas
class InventoryMetric(BaseModel):
    total_products: int
    total_variants: int
    low_stock_items: int
    out_of_stock_items: int
    total_inventory_value: Decimal


class ProductMovement(BaseModel):
    product_id: int
    product_name: str
    variant_name: str
    current_stock: int
    sold_quantity: int
    movement_velocity: float  # Sales per day


class InventoryReportData(BaseModel):
    metrics: InventoryMetric
    low_stock_products: List[ProductMovement]
    top_moving_products: List[ProductMovement]
    inventory_by_category: Dict[str, int]


# Clients Report Schemas
class ClientMetric(BaseModel):
    total_clients: int
    active_clients: int  # Clients with purchases in the period
    new_clients: int
    avg_order_value: Decimal
    customer_lifetime_value: Decimal


class TopClient(BaseModel):
    client_id: int
    client_name: str
    phone: Optional[str]
    total_purchases: Decimal
    order_count: int
    last_purchase_date: datetime


class ClientsReportData(BaseModel):
    metrics: ClientMetric
    top_clients: List[TopClient]
    client_acquisition_trend: List[Dict[str, Any]]
    clients_by_segment: Dict[str, int]


# Performance Report Schemas
class PerformanceMetric(BaseModel):
    revenue_growth_rate: float
    sales_growth_rate: float
    profit_margin_trend: float
    inventory_turnover: float
    customer_retention_rate: float


class KPIData(BaseModel):
    name: str
    current_value: float
    target_value: float
    achievement_percentage: float
    trend: str  # "up", "down", "stable"


class PerformanceReportData(BaseModel):
    metrics: PerformanceMetric
    kpis: List[KPIData]
    monthly_performance: List[Dict[str, Any]]


# Custom Report Schemas
class CustomReportConfig(BaseModel):
    selected_metrics: List[str]
    chart_types: List[str]
    grouping: Optional[str] = None
    custom_filters: Optional[Dict[str, Any]] = None


class CustomReportData(BaseModel):
    config: CustomReportConfig
    data: Dict[str, Any]
    charts: List[Dict[str, Any]]


# Union type for all report data types
ReportData = Union[
    SalesReportData,
    FinanceReportData,
    InventoryReportData,
    ClientsReportData,
    PerformanceReportData,
    CustomReportData
]


# Response schemas
class ReportResponse(BaseModel):
    id: Optional[int] = None
    report_type: ReportTypeEnum
    name: Optional[str] = None
    data: ReportData
    generated_at: datetime
    execution_time_ms: Optional[int] = None


class ReportListItem(BaseModel):
    id: int
    name: str
    report_type: ReportTypeEnum
    status: str
    created_at: datetime
    generated_at: Optional[datetime]
    file_path: Optional[str]


class ReportListResponse(BaseModel):
    reports: List[ReportListItem]
    total: int
    page: int
    limit: int


# Template schemas
class ReportTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: ReportTypeEnum
    config_template: Dict[str, Any]


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplateResponse(ReportTemplateBase):
    id: int
    is_system_template: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Export request schema
class ReportExportRequest(BaseModel):
    report_id: Optional[int] = None
    report_type: ReportTypeEnum
    format: ReportFormatEnum
    filters: Optional[ReportFilters] = None
    include_charts: bool = True
