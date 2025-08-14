from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.services.sale_service import SaleService
from app.schemas.sale import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    SaleFilter,
    SaleItemResponse,
    PaginatedSaleResponse,
    DebtPaymentRequest,
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models import Sale, Client, Transaction
from app.models.transaction import TransactionType

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=ResponseModel)
async def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new sale."""
    sale_service = SaleService(db)
    try:
        sale = sale_service.create_sale(sale_data, current_user)

        sale_items = []
        for item in sale.items:
            sale_items.append(
                SaleItemResponse(
                    id=item.id,
                    product_variant_id=item.product_variant_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    product_variant_sku=item.product_variant.sku,
                    product_name=item.product_variant.product.name,
                    color_name=item.product_variant.color.name,
                    size_name=item.product_variant.size.name,
                    created_at=item.created_at.isoformat(),
                )
            )

        return ResponseModel(
            success=True,
            data=SaleResponse(
                id=sale.id,
                receipt_number=sale.receipt_number,
                client_id=sale.client_id,
                total_amount=sale.total_amount,
                paid_amount=sale.paid_amount,
                payment_method=sale.payment_method,
                status=sale.status,
                notes=sale.notes,
                created_at=sale.created_at.isoformat(),
                updated_at=sale.updated_at.isoformat() if sale.updated_at else None,
                items=sale_items,
                client_name=f"{sale.client.first_name} {sale.client.last_name}"
                if sale.client
                else None,
            ),
            message="Sale created successfully",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.get("/{sale_id}", response_model=ResponseModel)
async def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific sale by ID."""
    sale_service = SaleService(db)
    sale = sale_service.get_sale(sale_id)

    if not sale:
        return ResponseModel(success=False, message="Sale not found")

    # Convert sale items to response format
    sale_items = []
    for item in sale.items:
        sale_items.append(
            SaleItemResponse(
                id=item.id,
                product_variant_id=item.product_variant_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product_variant_sku=item.product_variant.sku,
                product_name=item.product_variant.product.name,
                color_name=item.product_variant.color.name,
                size_name=item.product_variant.size.name,
                created_at=item.created_at.isoformat(),
            )
        )

    return ResponseModel(
        success=True,
        data=SaleResponse(
            id=sale.id,
            receipt_number=sale.receipt_number,
            client_id=sale.client_id,
            total_amount=sale.total_amount,
            paid_amount=sale.paid_amount,
            payment_method=sale.payment_method,
            status=sale.status,
            notes=sale.notes,
            created_at=sale.created_at.isoformat(),
            updated_at=sale.updated_at.isoformat() if sale.updated_at else None,
            items=sale_items,
            client_name=f"{sale.client.first_name} {sale.client.last_name}"
            if sale.client
            else None,
        ),
        message="Sale retrieved successfully",
    )


@router.get("/", response_model=ResponseModel)
async def get_sales(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    status: Optional[str] = Query(None, description="Filter by sale status"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all sales with filtering and pagination."""
    filters = SaleFilter(
        client_id=client_id,
        payment_method=payment_method,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
    )

    sale_service = SaleService(db)
    sales, pagination = sale_service.get_sales(filters)

    # Convert to response format
    sale_responses = []
    for sale in sales:
        sale_items = []
        for item in sale.items:
            sale_items.append(
                SaleItemResponse(
                    id=item.id,
                    product_variant_id=item.product_variant_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    product_variant_sku=item.product_variant.sku,
                    product_name=item.product_variant.product.name,
                    color_name=item.product_variant.color.name,
                    size_name=item.product_variant.size.name,
                    created_at=item.created_at.isoformat(),
                )
            )

        sale_responses.append(
            SaleResponse(
                id=sale.id,
                receipt_number=sale.receipt_number,
                client_id=sale.client_id,
                total_amount=sale.total_amount,
                paid_amount=sale.paid_amount,
                payment_method=sale.payment_method,
                status=sale.status,
                notes=sale.notes,
                created_at=sale.created_at.isoformat(),
                updated_at=sale.updated_at.isoformat() if sale.updated_at else None,
                items=sale_items,
                client_name=f"{sale.client.first_name} {sale.client.last_name}"
                if sale.client
                else None,
            )
        )

    return ResponseModel(
        success=True,
        data=PaginatedResponse(items=sale_responses, pagination=pagination),
        message="Sales retrieved successfully",
    )


@router.get("/stats/", response_model=ResponseModel)
async def get_sales_stats(
    start_date: Optional[date] = Query(None, description="Start date for stats"),
    end_date: Optional[date] = Query(None, description="End date for stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get sales statistics."""
    query = db.query(Sale)

    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    sales = query.all()

    total_sales = len(sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    avg_order_value = total_revenue / total_sales if total_sales > 0 else 0
    completed_sales = len([s for s in sales if s.status == "completed"])

    return ResponseModel(
        success=True,
        data={
            "total_sales": total_sales,
            "total_revenue": float(total_revenue),
            "avg_order_value": float(avg_order_value),
            "completed_sales": completed_sales,
        },
        message="Sales statistics retrieved successfully",
    )


@router.post("/debt-payment", response_model=ResponseModel)
async def process_debt_payment(
    payment_data: DebtPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Process a debt payment for a client."""
    client = db.query(Client).filter(Client.id == payment_data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.debt_amount < payment_data.payment_amount:
        raise HTTPException(
            status_code=400, detail="Payment amount exceeds debt amount"
        )

    # Update client debt
    client.debt_amount -= payment_data.payment_amount
    db.commit()

    # Create transaction record
    transaction = Transaction(
        client_id=payment_data.client_id,
        user_id=current_user.id,
        amount=payment_data.payment_amount,
        transaction_type=TransactionType.DEBT_PAYMENT,
        description=f"Debt payment of {payment_data.payment_amount}",
        created_at=datetime.utcnow(),
    )
    db.add(transaction)
    db.commit()

    return ResponseModel(
        success=True,
        data={
            "client_id": payment_data.client_id,
            "payment_amount": float(payment_data.payment_amount),
            "new_debt_amount": float(client.debt_amount),
        },
        message="Debt payment processed successfully",
    )


@router.get("/client/{client_id}/debt-history", response_model=ResponseModel)
async def get_client_debt_history(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get debt history for a specific client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get all transactions for this client
    transactions = (
        db.query(Transaction)
        .filter(Transaction.client_id == client_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    debt_history = []
    balance = 0

    for transaction in transactions:
        if transaction.transaction_type == TransactionType.SALE:
            balance += transaction.amount
        elif transaction.transaction_type == TransactionType.DEBT_PAYMENT:
            balance -= transaction.amount

        debt_history.append(
            {
                "id": transaction.id,
                "type": transaction.transaction_type.value,
                "amount": float(transaction.amount),
                "balance": float(balance),
                "created_at": transaction.created_at.isoformat(),
            }
        )

    return ResponseModel(
        success=True,
        data=debt_history,
        message="Client debt history retrieved successfully",
    )


@router.patch("/{sale_id}/cancel", response_model=ResponseModel)
async def cancel_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a sale."""
    sale_service = SaleService(db)
    try:
        sale = sale_service.cancel_sale(sale_id)
        if not sale:
            return ResponseModel(success=False, message="Sale not found")

        return ResponseModel(success=True, message="Sale cancelled successfully")
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.post("/{sale_id}/pay-debt", response_model=ResponseModel)
async def pay_sale_debt(
    sale_id: int,
    payment_amount: Decimal,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Pay debt for a specific sale."""
    sale_service = SaleService(db)
    try:
        sale = sale_service.pay_debt(sale_id, payment_amount, current_user)
        
        # Convert sale items to response format
        sale_items = []
        for item in sale.items:
            sale_items.append(
                SaleItemResponse(
                    id=item.id,
                    product_variant_id=item.product_variant_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    product_variant_sku=item.product_variant.sku,
                    product_name=item.product_variant.product.name,
                    color_name=item.product_variant.color.name,
                    size_name=item.product_variant.size.name,
                    created_at=item.created_at.isoformat(),
                )
            )

        return ResponseModel(
            success=True,
            data=SaleResponse(
                id=sale.id,
                receipt_number=sale.receipt_number,
                client_id=sale.client_id,
                total_amount=sale.total_amount,
                paid_amount=sale.paid_amount,
                payment_method=sale.payment_method,
                status=sale.status,
                notes=sale.notes,
                created_at=sale.created_at.isoformat(),
                updated_at=sale.updated_at.isoformat() if sale.updated_at else None,
                items=sale_items,
                client_name=f"{sale.client.first_name} {sale.client.last_name}"
                if sale.client
                else None,
            ),
            message="Debt payment processed successfully",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.get("/client/{client_id}/debts", response_model=ResponseModel)
async def get_client_debts(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all debt sales for a specific client."""
    sale_service = SaleService(db)
    debts = sale_service.get_client_debts(client_id)
    
    # Convert to response format
    debt_responses = []
    for sale in debts:
        sale_items = []
        for item in sale.items:
            sale_items.append(
                SaleItemResponse(
                    id=item.id,
                    product_variant_id=item.product_variant_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    product_variant_sku=item.product_variant.sku,
                    product_name=item.product_variant.product.name,
                    color_name=item.product_variant.color.name,
                    size_name=item.product_variant.size.name,
                    created_at=item.created_at.isoformat(),
                )
            )

        debt_responses.append(
            SaleResponse(
                id=sale.id,
                receipt_number=sale.receipt_number,
                client_id=sale.client_id,
                total_amount=sale.total_amount,
                paid_amount=sale.paid_amount,
                payment_method=sale.payment_method,
                status=sale.status,
                notes=sale.notes,
                created_at=sale.created_at.isoformat(),
                updated_at=sale.updated_at.isoformat() if sale.updated_at else None,
                items=sale_items,
                client_name=f"{sale.client.first_name} {sale.client.last_name}"
                if sale.client
                else None,
            )
        )

    return ResponseModel(
        success=True,
        data=debt_responses,
        message="Client debts retrieved successfully",
    )


@router.get("/debt-trend", response_model=ResponseModel)
async def get_debt_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to get trend data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get debt trend data over time."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Generate date range
    trend_data = []
    current_date = start_date

    while current_date <= end_date:
        # Get total debt amount for this date
        total_debt = (
            db.query(func.coalesce(func.sum(Client.debt_amount), 0))
            .filter(
                and_(
                    Client.debt_amount > 0,
                    Client.created_at <= current_date
                )
            )
            .scalar()
        ) or 0

        # Get number of clients with debt for this date
        client_count = (
            db.query(func.count(Client.id))
            .filter(
                and_(
                    Client.debt_amount > 0,
                    Client.created_at <= current_date
                )
            )
            .scalar()
        ) or 0

        trend_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "total_debt": float(total_debt),
            "client_count": client_count
        })

        current_date += timedelta(days=1)

    return ResponseModel(
        success=True,
        data=trend_data,
        message="Debt trend data retrieved successfully",
    )


@router.get("/payment-trend", response_model=ResponseModel)
async def get_payment_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to get payment trend data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get payment trend data over time."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Generate date range
    trend_data = []
    current_date = start_date

    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        # Get total payment amount for this date (debt payments only)
        total_payments = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                and_(
                    Transaction.transaction_type == TransactionType.DEBT_PAYMENT,
                    Transaction.created_at >= current_date,
                    Transaction.created_at < next_date
                )
            )
            .scalar()
        ) or 0

        # Get number of payment transactions for this date
        payment_count = (
            db.query(func.count(Transaction.id))
            .filter(
                and_(
                    Transaction.transaction_type == TransactionType.DEBT_PAYMENT,
                    Transaction.created_at >= current_date,
                    Transaction.created_at < next_date
                )
            )
            .scalar()
        ) or 0

        trend_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "total_payments": float(total_payments),
            "payment_count": payment_count
        })

        current_date += timedelta(days=1)

    return ResponseModel(
        success=True,
        data=trend_data,
        message="Payment trend data retrieved successfully",
    )
