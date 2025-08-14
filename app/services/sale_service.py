from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from app.models.sale import Sale, SaleItem, SaleStatus, PaymentMethod
from app.models.product_variant import ProductVariant
from app.models.client import Client
from app.models.transaction import Transaction, TransactionType
from app.schemas.sale import SaleCreate, SaleUpdate, SaleFilter
from app.utils.helpers import (
    generate_receipt_number,
    calculate_total_price,
    paginate_query,
    calculate_pagination_info,
)
from fastapi import HTTPException, status
from app.models.user import User

class SaleService:
    def __init__(self, db: Session):
        self.db = db

    def create_sale(self, sale_data: SaleCreate, current_user: User) -> Sale:
        """Create a new sale with items."""
        if sale_data.client_id:
            client = (
                self.db.query(Client).filter(Client.id == sale_data.client_id).first()
            )
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Client not found"
                )

        total_amount = Decimal("0")
        sale_items = []

        for item_data in sale_data.items:
            product_variant = (
                self.db.query(ProductVariant)
                .filter(ProductVariant.id == item_data.product_variant_id)
                .first()
            )
            if not product_variant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product variant with ID {item_data.product_variant_id} not found",
                )

            if product_variant.stock_quantity < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product variant {product_variant.sku}",
                )

            # Calculate item total
            item_total = item_data.unit_price * item_data.quantity
            total_amount += item_total

            sale_items.append(
                {"product_variant": product_variant, "data": item_data, "total": item_total}
            )

        if sale_data.paid_amount > total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paid amount cannot exceed total amount"
            )

        if sale_data.paid_amount == 0:
            sale_status = SaleStatus.DEBT
        elif sale_data.paid_amount == total_amount:
            sale_status = SaleStatus.COMPLETED
        else:
            sale_status = SaleStatus.PARTIALLY_PAID
            
            
        if sale_data.paid_amount < total_amount:
            client.debt_amount += total_amount - sale_data.paid_amount
            self.db.commit()

        # Create sale
        receipt_number = generate_receipt_number()
        db_sale = Sale(
            receipt_number=receipt_number,
            client_id=sale_data.client_id,
            total_amount=total_amount,
            paid_amount=sale_data.paid_amount,
            payment_method=sale_data.payment_method,
            status=sale_status,
            notes=sale_data.notes,
            user_id=current_user.id,
        )

        self.db.add(db_sale)
        self.db.flush()  # Get the sale ID

        # Create sale items and update stock
        for item_info in sale_items:
            sale_item = SaleItem(
                sale_id=db_sale.id,
                product_variant_id=item_info["product_variant"].id,
                quantity=item_info["data"].quantity,
                unit_price=item_info["data"].unit_price,
                total_price=item_info["total"],
            )
            self.db.add(sale_item)

            # Update product variant stock
            item_info["product_variant"].stock_quantity -= item_info["data"].quantity

        # Create transaction record only for paid amount
        if sale_data.paid_amount > 0:
            transaction = Transaction(
                transaction_type=TransactionType.SALE,
                amount=sale_data.paid_amount,
                description=f"Sale {receipt_number} - Paid amount",
                sale_id=db_sale.id,
                client_id=sale_data.client_id,
                user_id=current_user.id,
            )
            self.db.add(transaction)

        self.db.commit()
        self.db.refresh(db_sale)
        return db_sale

    def get_sale(self, sale_id: int) -> Optional[Sale]:
        """Get a sale by ID."""
        return self.db.query(Sale).filter(Sale.id == sale_id).first()

    def get_sales(self, filters: SaleFilter) -> Tuple[List[Sale], dict]:
        """Get sales with filtering and pagination."""
        query = self.db.query(Sale)

        # Apply filters
        if filters.client_id:
            query = query.filter(Sale.client_id == filters.client_id)

        if filters.payment_method:
            query = query.filter(Sale.payment_method == filters.payment_method)

        if filters.status:
            query = query.filter(Sale.status == filters.status)

        if filters.start_date:
            start_date = datetime.fromisoformat(filters.start_date)
            query = query.filter(Sale.created_at >= start_date)

        if filters.end_date:
            end_date = datetime.fromisoformat(filters.end_date)
            query = query.filter(Sale.created_at <= end_date)

        # Get total count
        total = query.count()

        # Set working directory
        query = query.order_by(Sale.created_at.desc())
        # Apply pagination
        query = paginate_query(query, filters.page, filters.size)

        # Get results
        sales = query.all()

        # Calculate pagination info
        pagination = calculate_pagination_info(total, filters.page, filters.size)

        return sales, pagination

    def cancel_sale(self, sale_id: int) -> Optional[Sale]:
        """Cancel a sale and restore stock."""
        sale = self.get_sale(sale_id)
        if not sale:
            return None

        if sale.status == SaleStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sale is already cancelled",
            )

        # Restore stock
        for item in sale.items:
            product_variant = (
                self.db.query(ProductVariant).filter(ProductVariant.id == item.product_variant_id).first()
            )
            if product_variant:
                product_variant.stock_quantity += item.quantity

        # Update sale status
        sale.status = SaleStatus.CANCELLED

        # Create refund transaction
        transaction = Transaction(
            type=TransactionType.REFUND,
            amount=-sale.total_amount, # Changed from final_amount to total_amount
            description=f"Refund for cancelled sale {sale.receipt_number}",
            sale_id=sale.id,
            client_id=sale.client_id,
            reference_number=f"REF-{sale.receipt_number}",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(sale)
        return sale

    def get_sales_summary(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> dict:
        """Get sales summary for a period."""
        query = self.db.query(Sale).filter(Sale.status == SaleStatus.COMPLETED)

        if start_date:
            query = query.filter(Sale.created_at >= start_date)

        if end_date:
            query = query.filter(Sale.created_at <= end_date)

        total_sales = query.count()
        total_revenue = query.with_entities(
            func.sum(Sale.total_amount) # Changed from final_amount to total_amount
        ).scalar() or Decimal("0")

        # Get sales by payment method
        payment_methods = (
            query.with_entities(
                Sale.payment_method,
                func.count(Sale.id).label("count"),
                func.sum(Sale.total_amount).label("total"), # Changed from final_amount to total_amount
            )
            .group_by(Sale.payment_method)
            .all()
        )

        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "payment_methods": [
                {"method": pm.payment_method, "count": pm.count, "total": pm.total}
                for pm in payment_methods
            ],
        }

    def get_recent_sales(self, limit: int = 10) -> List[Sale]:
        """Get recent sales."""
        return (
            self.db.query(Sale)
            .filter(Sale.status == SaleStatus.COMPLETED)
            .order_by(Sale.created_at.desc())
            .limit(limit)
            .all()
        )

    def pay_debt(self, sale_id: int, payment_amount: Decimal, current_user: User) -> Sale:
        """Pay remaining debt for a sale."""
        sale = self.get_sale(sale_id)
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        if sale.status == SaleStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot pay debt for cancelled sale"
            )

        if sale.status == SaleStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sale is already fully paid"
            )

        remaining_debt = sale.total_amount - sale.paid_amount
        if payment_amount > remaining_debt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount exceeds remaining debt. Remaining debt: {remaining_debt}"
            )

        # Update paid amount
        sale.paid_amount += payment_amount

        # Update sale status
        if sale.paid_amount == sale.total_amount:
            sale.status = SaleStatus.COMPLETED
        else:
            sale.status = SaleStatus.PARTIALLY_PAID

        # Create transaction for the payment
        transaction = Transaction(
            transaction_type=TransactionType.DEBT_PAYMENT,
            amount=payment_amount,
            description=f"Debt payment for sale {sale.receipt_number}",
            sale_id=sale.id,
            client_id=sale.client_id,
            user_id=current_user.id,
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(sale)
        return sale

    def get_client_debts(self, client_id: int) -> List[Sale]:
        """Get all debt sales for a specific client."""
        return (
            self.db.query(Sale)
            .filter(
                Sale.client_id == client_id,
                Sale.status.in_([SaleStatus.DEBT, SaleStatus.PARTIALLY_PAID])
            )
            .order_by(Sale.created_at.desc())
            .all()
        )
