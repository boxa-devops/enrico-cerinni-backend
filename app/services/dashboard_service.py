from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import hashlib
import json
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.client import Client
from app.models.sale import Sale, SaleStatus, SaleItem
from app.models.transaction import Transaction
from app.models.expense import Expense
from app.services.product_service import ProductService
from app.services.sale_service import SaleService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)
        self.sale_service = SaleService(db)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache

    def _get_cache_key(self, method_name: str, **kwargs) -> str:
        """Generate cache key for method with parameters."""
        key_data = {"method": method_name, **kwargs}
        return hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()

    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.now().timestamp() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[cache_key]
        return None

    def _set_cache_data(self, cache_key: str, data: Any) -> None:
        """Set data in cache with timestamp."""
        self._cache[cache_key] = (data, datetime.now().timestamp())

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics."""
        # Basic counts
        total_products = self.db.query(Product).count()
        total_clients = self.db.query(Client).count()
        total_sales = (
            self.db.query(Sale).filter(Sale.status == SaleStatus.COMPLETED).count()
        )

        # Revenue calculations
        total_revenue = self.db.query(func.sum(Sale.total_amount)).filter(
            Sale.status == SaleStatus.COMPLETED
        ).scalar() or Decimal("0")

        # Low stock product variants
        low_stock_variants = (
            self.db.query(ProductVariant)
            .filter(ProductVariant.stock_quantity <= ProductVariant.min_stock_level)
            .all()
        )
        low_stock_count = len(low_stock_variants)

        # Recent sales (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_sales = (
            self.db.query(Sale)
            .filter(Sale.status == SaleStatus.COMPLETED, Sale.created_at >= week_ago)
            .order_by(desc(Sale.created_at))
            .limit(5)
            .all()
        )

        recent_sales_data = []
        for sale in recent_sales:
            recent_sales_data.append(
                {
                    "id": sale.id,
                    "receipt_number": sale.receipt_number,
                    "amount": float(sale.total_amount),
                    "client_name": f"{sale.client.first_name} {sale.client.last_name}"
                    if sale.client
                    else "Walk-in",
                    "created_at": sale.created_at.isoformat(),
                }
            )

        # Monthly revenue (last 6 months)
        monthly_revenue = []
        for i in range(6):
            month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)

            month_revenue = self.db.query(func.sum(Sale.total_amount)).filter(
                Sale.status == SaleStatus.COMPLETED,
                Sale.created_at >= month_start,
                Sale.created_at <= month_end,
            ).scalar() or Decimal("0")

            monthly_revenue.append(
                {
                    "month": month_start.strftime("%B %Y"),
                    "revenue": float(month_revenue),
                }
            )

        # Top products by sales
        top_products = (
            self.db.query(
                Product.name,
                func.sum(SaleItem.quantity).label("total_sold"),
                func.sum(SaleItem.total_price).label("total_revenue"),
            )
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .join(SaleItem, SaleItem.product_variant_id == ProductVariant.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(Sale.status == SaleStatus.COMPLETED)
            .group_by(Product.id, Product.name)
            .order_by(desc(func.sum(SaleItem.quantity)))
            .limit(5)
            .all()
        )

        top_products_data = []
        for product in top_products:
            top_products_data.append(
                {
                    "name": product.name,
                    "total_sold": int(product.total_sold),
                    "total_revenue": float(product.total_revenue),
                }
            )

        # Clients with debts
        clients_with_debts = (
            self.db.query(Client)
            .join(Sale)
            .filter(Sale.status.in_([SaleStatus.DEBT, SaleStatus.PARTIALLY_PAID]))
            .distinct()
            .count()
        )

        # Total orders count (all completed sales)
        total_orders = total_sales

        # Monthly expenses (basic calculation)
        month_ago = datetime.now() - timedelta(days=30)
        monthly_expenses = self.db.query(func.sum(func.abs(Transaction.amount))).filter(
            Transaction.amount < 0,
            Transaction.created_at >= month_ago
        ).scalar() or Decimal("0")

        return {
            "total_products": total_products,
            "total_clients": total_clients,
            "total_sales": total_sales,
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "clients_with_debts": clients_with_debts,
            "monthly_expenses": float(monthly_expenses),
            "low_stock_products": low_stock_count,
            "recent_sales": recent_sales_data,
            "monthly_revenue": monthly_revenue,
            "top_products": top_products_data,
        }

    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent financial transactions."""
        transactions = (
            self.db.query(Transaction)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
            .all()
        )

        transaction_data = []
        for transaction in transactions:
            transaction_data.append(
                {
                    "id": transaction.id,
                    "type": transaction.transaction_type.value if transaction.transaction_type else "UNKNOWN",
                    "amount": float(transaction.amount),
                    "description": transaction.description or "",
                    "created_at": transaction.created_at.isoformat(),
                }
            )

        return transaction_data

    def get_financial_summary(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get financial summary for a period."""
        query = self.db.query(Transaction)

        if start_date:
            query = query.filter(Transaction.created_at >= start_date)

        if end_date:
            query = query.filter(Transaction.created_at <= end_date)

        # Total transactions
        total_transactions = query.count()

        # Revenue (positive transactions)
        revenue = query.filter(Transaction.amount > 0).with_entities(
            func.sum(Transaction.amount)
        ).scalar() or Decimal("0")

        # Expenses (negative transactions)
        expenses = query.filter(Transaction.amount < 0).with_entities(
            func.sum(Transaction.amount)
        ).scalar() or Decimal("0")

        # Net profit
        net_profit = revenue + expenses  # expenses is negative

        # Transactions by type
        transactions_by_type = (
            query.with_entities(
                Transaction.type,
                func.count(Transaction.id).label("count"),
                func.sum(Transaction.amount).label("total"),
            )
            .group_by(Transaction.type)
            .all()
        )

        return {
            "total_transactions": total_transactions,
            "revenue": float(revenue),
            "expenses": float(abs(expenses)),
            "net_profit": float(net_profit),
            "transactions_by_type": [
                {"type": t.type.value, "count": t.count, "total": float(t.total)}
                for t in transactions_by_type
            ],
        }

    def _get_period_dates(self, period: str):
        """Get start and end dates for a given period."""
        now = datetime.now()
        
        if period == "1week":
            start_date = now - timedelta(days=7)
            periods = 7
            interval = "day"
        elif period == "1month":
            start_date = now - timedelta(days=30)
            periods = 7
            interval = "week"
        elif period == "3months":
            start_date = now - timedelta(days=90)
            periods = 12
            interval = "week"
        elif period == "6months":
            start_date = now - timedelta(days=180)
            periods = 6
            interval = "month"
        elif period == "1year":
            start_date = now - timedelta(days=365)
            periods = 12
            interval = "month"
        else:
            # Default to 1 month
            start_date = now - timedelta(days=30)
            periods = 7
            interval = "week"
            
        return start_date, now, periods, interval

    def get_cashflow_data(self, period: str = "1month") -> List[Dict[str, Any]]:
        """Get cashflow data for charts."""
        cache_key = self._get_cache_key("get_cashflow_data", period=period)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        start_date, end_date, periods, interval = self._get_period_dates(period)
        
        # Generate data points based on interval
        data = []
        
        if interval == "day":
            for i in range(periods):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                # Income from sales
                income = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= day_start,
                    Sale.created_at < day_end
                ).scalar() or Decimal("0")
                
                # Expenses from transactions
                expenses = self.db.query(func.sum(func.abs(Transaction.amount))).filter(
                    Transaction.amount < 0,
                    Transaction.created_at >= day_start,
                    Transaction.created_at < day_end
                ).scalar() or Decimal("0")
                
                data.append({
                    "month": day_start.strftime("%d/%m"),
                    "income": float(income),
                    "expenses": float(expenses),
                    "netFlow": float(income - expenses)
                })
                
        elif interval == "week":
            for i in range(periods):
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(weeks=1)
                
                # Income from sales
                income = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= week_start,
                    Sale.created_at < week_end
                ).scalar() or Decimal("0")
                
                # Expenses from transactions
                expenses = self.db.query(func.sum(func.abs(Transaction.amount))).filter(
                    Transaction.amount < 0,
                    Transaction.created_at >= week_start,
                    Transaction.created_at < week_end
                ).scalar() or Decimal("0")
                
                data.append({
                    "month": f"Hafta {i+1}",
                    "income": float(income),
                    "expenses": float(expenses),
                    "netFlow": float(income - expenses)
                })
                
        else:  # month interval
            for i in range(periods):
                month_start = start_date + timedelta(days=30*i)
                month_end = month_start + timedelta(days=30)
                
                # Income from sales
                income = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= month_start,
                    Sale.created_at < month_end
                ).scalar() or Decimal("0")
                
                # Expenses from transactions
                expenses = self.db.query(func.sum(func.abs(Transaction.amount))).filter(
                    Transaction.amount < 0,
                    Transaction.created_at >= month_start,
                    Transaction.created_at < month_end
                ).scalar() or Decimal("0")
                
                data.append({
                    "month": month_start.strftime("%b"),
                    "income": float(income),
                    "expenses": float(expenses),
                    "netFlow": float(income - expenses)
                })
        
        self._set_cache_data(cache_key, data)
        return data

    def get_profit_data(self, period: str = "1month") -> List[Dict[str, Any]]:
        """Get profit analysis data for charts."""
        cache_key = self._get_cache_key("get_profit_data", period=period)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        start_date, end_date, periods, interval = self._get_period_dates(period)
        
        data = []
        
        if interval == "day":
            for i in range(periods):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                # Revenue from sales
                revenue = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= day_start,
                    Sale.created_at < day_end
                ).scalar() or Decimal("0")
                
                # Cost estimation (60% of revenue as default)
                cost = revenue * Decimal("0.6")
                profit = revenue - cost
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                data.append({
                    "month": day_start.strftime("%d/%m"),
                    "revenue": float(revenue),
                    "cost": float(cost),
                    "profit": float(profit),
                    "margin": float(margin)
                })
                
        elif interval == "week":
            for i in range(periods):
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(weeks=1)
                
                revenue = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= week_start,
                    Sale.created_at < week_end
                ).scalar() or Decimal("0")
                
                cost = revenue * Decimal("0.6")
                profit = revenue - cost
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                data.append({
                    "month": f"Hafta {i+1}",
                    "revenue": float(revenue),
                    "cost": float(cost),
                    "profit": float(profit),
                    "margin": float(margin)
                })
                
        else:  # month interval
            for i in range(periods):
                month_start = start_date + timedelta(days=30*i)
                month_end = month_start + timedelta(days=30)
                
                revenue = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= month_start,
                    Sale.created_at < month_end
                ).scalar() or Decimal("0")
                
                cost = revenue * Decimal("0.6")
                profit = revenue - cost
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                data.append({
                    "month": month_start.strftime("%b"),
                    "revenue": float(revenue),
                    "cost": float(cost),
                    "profit": float(profit),
                    "margin": float(margin)
                })
        
        self._set_cache_data(cache_key, data)
        return data

    def get_sales_performance_data(self, period: str = "1month") -> List[Dict[str, Any]]:
        """Get sales performance data for charts."""
        cache_key = self._get_cache_key("get_sales_performance_data", period=period)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        start_date, end_date, periods, interval = self._get_period_dates(period)
        
        data = []
        previous_sales = 0
        
        if interval == "day":
            for i in range(periods):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                # Sales amount
                sales = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= day_start,
                    Sale.created_at < day_end
                ).scalar() or Decimal("0")
                
                # Number of orders
                orders = self.db.query(Sale).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= day_start,
                    Sale.created_at < day_end
                ).count()
                
                # Average order value
                avg_order = (sales / orders) if orders > 0 else 0
                
                # Growth calculation
                growth = 0
                if previous_sales > 0:
                    growth = ((float(sales) - previous_sales) / previous_sales) * 100
                previous_sales = float(sales)
                
                data.append({
                    "month": day_start.strftime("%d/%m"),
                    "sales": float(sales),
                    "orders": orders,
                    "avgOrder": float(avg_order),
                    "growth": growth
                })
                
        elif interval == "week":
            for i in range(periods):
                week_start = start_date + timedelta(weeks=i)
                week_end = week_start + timedelta(weeks=1)
                
                sales = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= week_start,
                    Sale.created_at < week_end
                ).scalar() or Decimal("0")
                
                orders = self.db.query(Sale).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= week_start,
                    Sale.created_at < week_end
                ).count()
                
                avg_order = (sales / orders) if orders > 0 else 0
                
                growth = 0
                if previous_sales > 0:
                    growth = ((float(sales) - previous_sales) / previous_sales) * 100
                previous_sales = float(sales)
                
                data.append({
                    "month": f"Hafta {i+1}",
                    "sales": float(sales),
                    "orders": orders,
                    "avgOrder": float(avg_order),
                    "growth": growth
                })
                
        else:  # month interval
            for i in range(periods):
                month_start = start_date + timedelta(days=30*i)
                month_end = month_start + timedelta(days=30)
                
                sales = self.db.query(func.sum(Sale.total_amount)).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= month_start,
                    Sale.created_at < month_end
                ).scalar() or Decimal("0")
                
                orders = self.db.query(Sale).filter(
                    Sale.status == SaleStatus.COMPLETED,
                    Sale.created_at >= month_start,
                    Sale.created_at < month_end
                ).count()
                
                avg_order = (sales / orders) if orders > 0 else 0
                
                growth = 0
                if previous_sales > 0:
                    growth = ((float(sales) - previous_sales) / previous_sales) * 100
                previous_sales = float(sales)
                
                data.append({
                    "month": month_start.strftime("%b"),
                    "sales": float(sales),
                    "orders": orders,
                    "avgOrder": float(avg_order),
                    "growth": growth
                })
        
        self._set_cache_data(cache_key, data)
        return data

    def get_expense_breakdown_data(self, period: str = "1month") -> List[Dict[str, Any]]:
        """Get expense breakdown data for charts."""
        cache_key = self._get_cache_key("get_expense_breakdown_data", period=period)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        start_date, end_date, periods, interval = self._get_period_dates(period)
        
        # Get expenses by category (using transaction descriptions as categories)
        expense_data = self.db.query(
            Transaction.description,
            func.sum(func.abs(Transaction.amount)).label("total_amount")
        ).filter(
            Transaction.amount < 0,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).group_by(Transaction.description).all()
        
        # Define colors for different expense categories
        colors = [
            "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", 
            "#06b6d4", "#64748b", "#f97316", "#84cc16", "#ec4899"
        ]
        
        data = []
        for i, expense in enumerate(expense_data[:10]):  # Limit to top 10 expenses
            data.append({
                "name": expense.description or "Boshqa xarajatlar",
                "value": float(expense.total_amount),
                "color": colors[i % len(colors)]
            })
        
        # If no expenses found, return sample data
        if not data:
            data = [
                {"name": "Xodimlar maoshi", "value": 0, "color": "#3b82f6"},
                {"name": "Mahsulot sotib olish", "value": 0, "color": "#10b981"},
                {"name": "Ijaraga to'lov", "value": 0, "color": "#f59e0b"},
                {"name": "Boshqa xarajatlar", "value": 0, "color": "#ef4444"},
            ]
        
        self._set_cache_data(cache_key, data)
        return data
