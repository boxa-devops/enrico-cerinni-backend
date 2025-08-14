from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardResponse, RecentTransaction
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=ResponseModel)
async def get_dashboard_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    dashboard_service = DashboardService(db)
    stats = dashboard_service.get_dashboard_stats()

    return ResponseModel(
        success=True, data=stats, message="Dashboard statistics retrieved successfully"
    )


@router.get("/recent-transactions", response_model=ResponseModel)
async def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50, description="Number of recent transactions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get recent financial transactions."""
    dashboard_service = DashboardService(db)
    transactions = dashboard_service.get_recent_transactions(limit)

    return ResponseModel(
        success=True,
        data=transactions,
        message="Recent transactions retrieved successfully",
    )


@router.get("/financial-summary", response_model=ResponseModel)
async def get_financial_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get financial summary for a period."""
    dashboard_service = DashboardService(db)

    # Parse dates if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            return ResponseModel(
                success=False, message="Invalid start date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            return ResponseModel(
                success=False, message="Invalid end date format. Use YYYY-MM-DD"
            )

    summary = dashboard_service.get_financial_summary(start_dt, end_dt)

    return ResponseModel(
        success=True, data=summary, message="Financial summary retrieved successfully"
    )


@router.get("/cashflow", response_model=ResponseModel)
async def get_cashflow_data(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get cashflow data for charts."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_cashflow_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Cashflow data retrieved successfully"
    )


@router.get("/profit-analysis", response_model=ResponseModel)
async def get_profit_data(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get profit analysis data for charts."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_profit_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Profit analysis data retrieved successfully"
    )


@router.get("/sales-performance", response_model=ResponseModel)
async def get_sales_performance_data(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get sales performance data for charts."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_sales_performance_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Sales performance data retrieved successfully"
    )


@router.get("/expense-breakdown", response_model=ResponseModel)
async def get_expense_breakdown_data(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get expense breakdown data for charts."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_expense_breakdown_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Expense breakdown data retrieved successfully"
    )


# Temporary test endpoints without authentication for dashboard testing
@router.get("/test/stats", response_model=ResponseModel)
async def get_dashboard_stats_test(db: Session = Depends(get_db)):
    """Test endpoint for dashboard stats without authentication."""
    dashboard_service = DashboardService(db)
    stats = dashboard_service.get_dashboard_stats()

    return ResponseModel(
        success=True, data=stats, message="Dashboard statistics retrieved successfully"
    )


@router.get("/test/cashflow", response_model=ResponseModel)
async def get_cashflow_data_test(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
):
    """Test endpoint for cashflow data without authentication."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_cashflow_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Cashflow data retrieved successfully"
    )


@router.get("/test/profit-analysis", response_model=ResponseModel)
async def get_profit_data_test(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
):
    """Test endpoint for profit analysis data without authentication."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_profit_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Profit analysis data retrieved successfully"
    )


@router.get("/test/sales-performance", response_model=ResponseModel)
async def get_sales_performance_data_test(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
):
    """Test endpoint for sales performance data without authentication."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_sales_performance_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Sales performance data retrieved successfully"
    )


@router.get("/test/expense-breakdown", response_model=ResponseModel)
async def get_expense_breakdown_data_test(
    period: str = Query("1month", description="Time period: 1week, 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db),
):
    """Test endpoint for expense breakdown data without authentication."""
    dashboard_service = DashboardService(db)
    data = dashboard_service.get_expense_breakdown_data(period)
    
    return ResponseModel(
        success=True, data=data, message="Expense breakdown data retrieved successfully"
    )


@router.get("/test/recent-transactions", response_model=ResponseModel)
async def get_recent_transactions_test(
    limit: int = Query(10, description="Number of recent transactions to retrieve"),
    db: Session = Depends(get_db),
):
    """Test endpoint for recent transactions without authentication."""
    dashboard_service = DashboardService(db)
    transactions = dashboard_service.get_recent_transactions(limit)
    
    return ResponseModel(
        success=True, data=transactions, message="Recent transactions retrieved successfully"
    )
