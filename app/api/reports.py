from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import time

from app.database import get_db
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportTypeEnum,
    ReportGenerateRequest,
    ReportResponse,
    ReportListResponse,
    ReportListItem,
    ReportTemplateCreate,
    ReportTemplateResponse,
    ReportExportRequest,
    ReportFilters,
    CustomReportConfig
)
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.report import ReportType, ReportExecution, ReportStatus

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ResponseModel)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a report based on type and filters."""
    start_time = time.time()
    report_service = ReportService(db)
    
    try:
        # Generate report based on type
        if request.report_type == ReportTypeEnum.SALES:
            data = report_service.generate_sales_report(request.filters)
        elif request.report_type == ReportTypeEnum.FINANCE:
            data = report_service.generate_finance_report(request.filters)
        elif request.report_type == ReportTypeEnum.INVENTORY:
            data = report_service.generate_inventory_report(request.filters)
        elif request.report_type == ReportTypeEnum.CLIENTS:
            data = report_service.generate_clients_report(request.filters)
        elif request.report_type == ReportTypeEnum.PERFORMANCE:
            data = report_service.generate_performance_report(request.filters)
        elif request.report_type == ReportTypeEnum.CUSTOM:
            # For custom reports, we need additional config
            config = CustomReportConfig(
                selected_metrics=["revenue", "sales"],
                chart_types=["bar", "line"]
            )
            data = report_service.generate_custom_report(config, request.filters)
        else:
            raise HTTPException(status_code=400, detail="Unsupported report type")
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Save report if requested
        report_id = None
        if request.save_report and request.name:
            saved_report = report_service.save_report(
                report_type=ReportType(request.report_type.value),
                name=request.name,
                data=data.dict(),
                user_id=current_user.id
            )
            report_id = saved_report.id
        
        # Log execution
        execution = ReportExecution(
            report_type=ReportType(request.report_type.value),
            parameters=request.dict(),
            status=ReportStatus.COMPLETED,
            execution_time_ms=execution_time,
            user_id=current_user.id,
            started_at=datetime.fromtimestamp(start_time),
            completed_at=datetime.now()
        )
        db.add(execution)
        db.commit()
        
        response = ReportResponse(
            id=report_id,
            report_type=request.report_type,
            name=request.name,
            data=data,
            generated_at=datetime.now(),
            execution_time_ms=execution_time
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message=f"{request.report_type.value.title()} report generated successfully"
        )
        
    except Exception as e:
        # Log failed execution
        execution = ReportExecution(
            report_type=ReportType(request.report_type.value),
            parameters=request.dict(),
            status=ReportStatus.FAILED,
            error_message=str(e),
            user_id=current_user.id,
            started_at=datetime.fromtimestamp(start_time),
            completed_at=datetime.now()
        )
        db.add(execution)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/sales", response_model=ResponseModel)
async def get_sales_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    client_ids: Optional[List[int]] = Query(None, description="Client IDs to filter"),
    payment_methods: Optional[List[str]] = Query(None, description="Payment methods to filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get sales report with optional filters."""
    report_service = ReportService(db)
    
    # Build filters
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    if client_ids:
        filters.client_ids = client_ids
    if payment_methods:
        filters.payment_methods = payment_methods
    
    data = report_service.generate_sales_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Sales report generated successfully"
    )


@router.get("/finance", response_model=ResponseModel)
async def get_finance_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get finance report with optional filters."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_finance_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Finance report generated successfully"
    )


@router.get("/inventory", response_model=ResponseModel)
async def get_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get inventory report."""
    report_service = ReportService(db)
    data = report_service.generate_inventory_report()
    
    return ResponseModel(
        success=True,
        data=data,
        message="Inventory report generated successfully"
    )


@router.get("/clients", response_model=ResponseModel)
async def get_clients_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get clients report with optional filters."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_clients_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Clients report generated successfully"
    )


@router.get("/performance", response_model=ResponseModel)
async def get_performance_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get performance report with optional filters."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_performance_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Performance report generated successfully"
    )


@router.get("/saved", response_model=ResponseModel)
async def get_saved_reports(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get user's saved reports."""
    report_service = ReportService(db)
    offset = (page - 1) * limit
    
    reports = report_service.get_saved_reports(current_user.id, limit, offset)
    
    # Convert to list items
    report_items = []
    for report in reports:
        report_items.append(ReportListItem(
            id=report.id,
            name=report.name,
            report_type=ReportTypeEnum(report.report_type.value),
            status=report.status.value,
            created_at=report.created_at,
            generated_at=report.generated_at,
            file_path=report.file_path
        ))
    
    # Get total count
    total = len(reports)  # Simplified - should be a separate count query
    
    response = ReportListResponse(
        reports=report_items,
        total=total,
        page=page,
        limit=limit
    )
    
    return ResponseModel(
        success=True,
        data=response,
        message="Saved reports retrieved successfully"
    )


@router.get("/templates", response_model=ResponseModel)
async def get_report_templates(
    report_type: Optional[ReportTypeEnum] = Query(None, description="Filter by report type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get available report templates."""
    report_service = ReportService(db)
    
    report_type_filter = ReportType(report_type.value) if report_type else None
    templates = report_service.get_report_templates(report_type_filter)
    
    template_responses = []
    for template in templates:
        template_responses.append(ReportTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            report_type=ReportTypeEnum(template.report_type.value),
            config_template=template.config_template,
            is_system_template=template.is_system_template,
            is_active=template.is_active,
            created_at=template.created_at
        ))
    
    return ResponseModel(
        success=True,
        data=template_responses,
        message="Report templates retrieved successfully"
    )


@router.post("/export", response_model=ResponseModel)
async def export_report(
    request: ReportExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export report in specified format."""
    # This would implement actual file export functionality
    # For now, return a placeholder response
    
    return ResponseModel(
        success=True,
        data={"download_url": "/reports/download/123", "expires_at": "2024-01-01T00:00:00Z"},
        message=f"Report export initiated. Format: {request.format.value}"
    )


# Test endpoints without authentication
@router.get("/test/sales", response_model=ResponseModel)
async def get_sales_report_test(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Test endpoint for sales report without authentication."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_sales_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Sales report generated successfully"
    )


@router.get("/test/finance", response_model=ResponseModel)
async def get_finance_report_test(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Test endpoint for finance report without authentication."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_finance_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Finance report generated successfully"
    )


@router.get("/test/inventory", response_model=ResponseModel)
async def get_inventory_report_test(db: Session = Depends(get_db)):
    """Test endpoint for inventory report without authentication."""
    report_service = ReportService(db)
    data = report_service.generate_inventory_report()
    
    return ResponseModel(
        success=True,
        data=data,
        message="Inventory report generated successfully"
    )


@router.get("/test/clients", response_model=ResponseModel)
async def get_clients_report_test(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Test endpoint for clients report without authentication."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_clients_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Clients report generated successfully"
    )


@router.get("/test/performance", response_model=ResponseModel)
async def get_performance_report_test(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Test endpoint for performance report without authentication."""
    report_service = ReportService(db)
    
    filters = ReportFilters()
    if start_date or end_date:
        from app.schemas.report import DateRangeFilter
        filters.date_range = DateRangeFilter()
        if start_date:
            try:
                filters.date_range.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        if end_date:
            try:
                filters.date_range.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
    
    data = report_service.generate_performance_report(filters)
    
    return ResponseModel(
        success=True,
        data=data,
        message="Performance report generated successfully"
    )
