from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json

from app.models.sale import Sale, SaleItem, PaymentMethod, SaleStatus
from app.models.client import Client
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.models.report import Report, ReportTemplate, ReportExecution, ReportType
from app.schemas.report import (
    ReportFilters,
    SalesReportData, SalesMetric, TopProduct, SalesTrendPoint,
    FinanceReportData, FinanceMetric, ExpenseBreakdown, MonthlyFinanceData, PaymentMethodBreakdown,
    InventoryReportData, InventoryMetric, ProductMovement,
    ClientsReportData, ClientMetric, TopClient,
    PerformanceReportData, PerformanceMetric, KPIData,
    CustomReportData, CustomReportConfig
)


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def _apply_date_filter(self, query, date_field, filters: Optional[ReportFilters]):
        """Apply date range filter to query."""
        if not filters or not filters.date_range:
            return query
        
        if filters.date_range.start_date:
            query = query.filter(date_field >= filters.date_range.start_date)
        
        if filters.date_range.end_date:
            query = query.filter(date_field <= filters.date_range.end_date)
        
        return query

    def _get_date_range(self, filters: Optional[ReportFilters]) -> Tuple[datetime, datetime]:
        """Get effective date range for reports."""
        if filters and filters.date_range:
            start_date = filters.date_range.start_date or (datetime.now() - timedelta(days=30))
            end_date = filters.date_range.end_date or datetime.now()
        else:
            # Default to last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date

    def generate_sales_report(self, filters: Optional[ReportFilters] = None) -> SalesReportData:
        """Generate comprehensive sales report."""
        start_date, end_date = self._get_date_range(filters)
        
        # Base query for sales in the period
        base_query = self.db.query(Sale).filter(
            Sale.created_at >= start_date,
            Sale.created_at <= end_date,
            Sale.status != SaleStatus.CANCELLED
        )
        
        # Apply additional filters
        if filters:
            if filters.client_ids:
                base_query = base_query.filter(Sale.client_id.in_(filters.client_ids))
            if filters.payment_methods:
                base_query = base_query.filter(Sale.payment_method.in_(filters.payment_methods))
            if filters.min_amount:
                base_query = base_query.filter(Sale.total_amount >= filters.min_amount)
            if filters.max_amount:
                base_query = base_query.filter(Sale.total_amount <= filters.max_amount)

        # Calculate metrics
        sales = base_query.all()
        total_revenue = sum(sale.total_amount for sale in sales)
        total_sales = len(sales)
        avg_order_value = total_revenue / total_sales if total_sales > 0 else Decimal('0')
        
        # Calculate conversion rate (placeholder - would need website traffic data)
        conversion_rate = 3.2  # Mock data
        
        metrics = SalesMetric(
            total_revenue=total_revenue,
            total_sales=total_sales,
            avg_order_value=avg_order_value,
            conversion_rate=conversion_rate
        )

        # Get top products
        top_products_query = (
            self.db.query(
                SaleItem.product_variant_id,
                func.sum(SaleItem.quantity).label('total_quantity'),
                func.sum(SaleItem.total_price).label('total_revenue')
            )
            .join(Sale)
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
            .group_by(SaleItem.product_variant_id)
            .order_by(desc('total_quantity'))
            .limit(10)
        )

        top_products = []
        for item in top_products_query.all():
            variant = self.db.query(ProductVariant).filter(
                ProductVariant.id == item.product_variant_id
            ).first()
            if variant:
                product = self.db.query(Product).filter(Product.id == variant.product_id).first()
                top_products.append(TopProduct(
                    product_id=product.id if product else 0,
                    product_name=product.name if product else "Unknown",
                    variant_name=f"{variant.size.name if variant.size else ''} {variant.color.name if variant.color else ''}".strip(),
                    sales_count=int(item.total_quantity),
                    total_revenue=item.total_revenue
                ))

        # Get sales trend (daily data)
        trend_query = (
            self.db.query(
                func.date(Sale.created_at).label('sale_date'),
                func.count(Sale.id).label('sales_count'),
                func.sum(Sale.total_amount).label('revenue')
            )
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
            .group_by(func.date(Sale.created_at))
            .order_by('sale_date')
        )

        sales_trend = []
        for item in trend_query.all():
            sales_trend.append(SalesTrendPoint(
                date=item.sale_date,
                sales_count=item.sales_count,
                revenue=item.revenue or Decimal('0')
            ))

        # Sales by payment method
        payment_query = (
            self.db.query(
                Sale.payment_method,
                func.sum(Sale.total_amount).label('total')
            )
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
            .group_by(Sale.payment_method)
        )

        sales_by_payment_method = {}
        for item in payment_query.all():
            sales_by_payment_method[item.payment_method.value] = item.total

        # Sales by category (placeholder - would need to join through product relationships)
        sales_by_category = {
            "Clothing": Decimal('5000000'),
            "Shoes": Decimal('3000000'),
            "Accessories": Decimal('1500000')
        }

        return SalesReportData(
            metrics=metrics,
            top_products=top_products,
            sales_trend=sales_trend,
            sales_by_payment_method=sales_by_payment_method,
            sales_by_category=sales_by_category
        )

    def generate_finance_report(self, filters: Optional[ReportFilters] = None) -> FinanceReportData:
        """Generate comprehensive finance report."""
        start_date, end_date = self._get_date_range(filters)
        
        # Calculate revenue from sales
        revenue_query = (
            self.db.query(func.sum(Sale.total_amount))
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
        )
        total_revenue = revenue_query.scalar() or Decimal('0')

        # Calculate expenses
        expense_query = (
            self.db.query(func.sum(Expense.amount))
            .filter(
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
        )
        total_expenses = expense_query.scalar() or Decimal('0')

        # Calculate metrics
        net_profit = total_revenue - total_expenses
        profit_margin = float((net_profit / total_revenue * 100)) if total_revenue > 0 else 0.0
        cash_flow = net_profit  # Simplified calculation

        metrics = FinanceMetric(
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_profit=net_profit,
            profit_margin=profit_margin,
            cash_flow=cash_flow
        )

        # Expense breakdown by category
        expense_breakdown_query = (
            self.db.query(
                Expense.category,
                func.sum(Expense.amount).label('total')
            )
            .filter(
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .group_by(Expense.category)
        )

        expense_categories = {item.category: item.total for item in expense_breakdown_query.all()}
        
        expense_breakdown = ExpenseBreakdown(
            suppliers=expense_categories.get('suppliers', Decimal('0')),
            salaries=expense_categories.get('salaries', Decimal('0')),
            rent=expense_categories.get('rent', Decimal('0')),
            utilities=expense_categories.get('utilities', Decimal('0')),
            marketing=expense_categories.get('marketing', Decimal('0')),
            other=sum(v for k, v in expense_categories.items() 
                     if k not in ['suppliers', 'salaries', 'rent', 'utilities', 'marketing'])
        )

        # Monthly data for the last 6 months
        monthly_data = []
        for i in range(6):
            month_start = (datetime.now().replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_revenue = (
                self.db.query(func.sum(Sale.total_amount))
                .filter(
                    Sale.created_at >= month_start,
                    Sale.created_at <= month_end,
                    Sale.status != SaleStatus.CANCELLED
                )
                .scalar() or Decimal('0')
            )
            
            month_expenses = (
                self.db.query(func.sum(Expense.amount))
                .filter(
                    Expense.created_at >= month_start,
                    Expense.created_at <= month_end
                )
                .scalar() or Decimal('0')
            )
            
            monthly_data.append(MonthlyFinanceData(
                month=month_start.strftime('%b %Y'),
                revenue=month_revenue,
                expenses=month_expenses,
                profit=month_revenue - month_expenses
            ))

        # Payment method breakdown
        payment_breakdown_query = (
            self.db.query(
                Sale.payment_method,
                func.sum(Sale.total_amount).label('total')
            )
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
            .group_by(Sale.payment_method)
        )

        payment_totals = {item.payment_method.value: item.total for item in payment_breakdown_query.all()}
        payment_methods = PaymentMethodBreakdown(
            cash=payment_totals.get('cash', Decimal('0')),
            card=payment_totals.get('card', Decimal('0')),
            transfer=payment_totals.get('transfer', Decimal('0')),
            debt=Decimal('0')  # Would need to calculate from unpaid amounts
        )

        return FinanceReportData(
            metrics=metrics,
            expense_breakdown=expense_breakdown,
            monthly_data=monthly_data,
            payment_methods=payment_methods
        )

    def generate_inventory_report(self, filters: Optional[ReportFilters] = None) -> InventoryReportData:
        """Generate inventory report."""
        # Count products and variants
        total_products = self.db.query(Product).count()
        total_variants = self.db.query(ProductVariant).count()
        
        # Low stock and out of stock items
        low_stock_items = self.db.query(ProductVariant).filter(
            ProductVariant.stock_quantity <= 10,
            ProductVariant.stock_quantity > 0
        ).count()
        
        out_of_stock_items = self.db.query(ProductVariant).filter(
            ProductVariant.stock_quantity == 0
        ).count()

        # Calculate inventory value
        inventory_value_query = (
            self.db.query(func.sum(ProductVariant.price * ProductVariant.stock_quantity))
            .filter(ProductVariant.stock_quantity > 0)
        )
        total_inventory_value = inventory_value_query.scalar() or Decimal('0')

        metrics = InventoryMetric(
            total_products=total_products,
            total_variants=total_variants,
            low_stock_items=low_stock_items,
            out_of_stock_items=out_of_stock_items,
            total_inventory_value=total_inventory_value
        )

        # Low stock products
        low_stock_products = []
        low_stock_variants = (
            self.db.query(ProductVariant)
            .filter(ProductVariant.stock_quantity <= 10, ProductVariant.stock_quantity > 0)
            .limit(20)
            .all()
        )

        for variant in low_stock_variants:
            product = self.db.query(Product).filter(Product.id == variant.product_id).first()
            if product:
                low_stock_products.append(ProductMovement(
                    product_id=product.id,
                    product_name=product.name,
                    variant_name=f"{variant.size.name if variant.size else ''} {variant.color.name if variant.color else ''}".strip(),
                    current_stock=variant.stock_quantity,
                    sold_quantity=0,  # Would need sales data calculation
                    movement_velocity=0.0  # Would need time-based calculation
                ))

        # Top moving products (placeholder)
        top_moving_products = low_stock_products[:10]  # Simplified

        # Inventory by category (placeholder)
        inventory_by_category = {
            "Clothing": 150,
            "Shoes": 80,
            "Accessories": 45
        }

        return InventoryReportData(
            metrics=metrics,
            low_stock_products=low_stock_products,
            top_moving_products=top_moving_products,
            inventory_by_category=inventory_by_category
        )

    def generate_clients_report(self, filters: Optional[ReportFilters] = None) -> ClientsReportData:
        """Generate clients report."""
        start_date, end_date = self._get_date_range(filters)
        
        # Basic client metrics
        total_clients = self.db.query(Client).count()
        
        # Active clients (with purchases in period)
        active_clients = (
            self.db.query(Client.id)
            .join(Sale)
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
            .distinct()
            .count()
        )

        # New clients in period
        new_clients = (
            self.db.query(Client)
            .filter(
                Client.created_at >= start_date,
                Client.created_at <= end_date
            )
            .count()
        )

        # Calculate average order value and CLV
        avg_order_value = Decimal('125000')  # Placeholder
        customer_lifetime_value = Decimal('500000')  # Placeholder

        metrics = ClientMetric(
            total_clients=total_clients,
            active_clients=active_clients,
            new_clients=new_clients,
            avg_order_value=avg_order_value,
            customer_lifetime_value=customer_lifetime_value
        )

        # Top clients by purchase amount
        top_clients_query = (
            self.db.query(
                Client.id,
                Client.first_name,
                Client.last_name,
                Client.phone,
                func.sum(Sale.total_amount).label('total_purchases'),
                func.count(Sale.id).label('order_count'),
                func.max(Sale.created_at).label('last_purchase')
            )
            .join(Sale)
            .filter(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date,
                Sale.status != SaleStatus.CANCELLED
            )
            .group_by(Client.id, Client.first_name, Client.last_name, Client.phone)
            .order_by(desc('total_purchases'))
            .limit(10)
        )

        top_clients = []
        for item in top_clients_query.all():
            top_clients.append(TopClient(
                client_id=item.id,
                client_name=f"{item.first_name} {item.last_name}",
                phone=item.phone,
                total_purchases=item.total_purchases,
                order_count=item.order_count,
                last_purchase_date=item.last_purchase
            ))

        # Client acquisition trend (placeholder)
        client_acquisition_trend = [
            {"month": "Jan", "new_clients": 12},
            {"month": "Feb", "new_clients": 18},
            {"month": "Mar", "new_clients": 15}
        ]

        # Clients by segment (placeholder)
        clients_by_segment = {
            "VIP": 25,
            "Regular": 180,
            "New": 45,
            "Inactive": 80
        }

        return ClientsReportData(
            metrics=metrics,
            top_clients=top_clients,
            client_acquisition_trend=client_acquisition_trend,
            clients_by_segment=clients_by_segment
        )

    def generate_performance_report(self, filters: Optional[ReportFilters] = None) -> PerformanceReportData:
        """Generate performance report."""
        # Calculate growth rates and performance metrics (placeholder data)
        metrics = PerformanceMetric(
            revenue_growth_rate=15.2,
            sales_growth_rate=12.8,
            profit_margin_trend=8.5,
            inventory_turnover=4.2,
            customer_retention_rate=78.5
        )

        # KPI data
        kpis = [
            KPIData(name="Revenue Target", current_value=87.5, target_value=100.0, achievement_percentage=87.5, trend="up"),
            KPIData(name="Sales Target", current_value=92.3, target_value=100.0, achievement_percentage=92.3, trend="up"),
            KPIData(name="Profit Margin", current_value=28.5, target_value=30.0, achievement_percentage=95.0, trend="stable"),
            KPIData(name="Customer Satisfaction", current_value=4.2, target_value=4.5, achievement_percentage=93.3, trend="up")
        ]

        # Monthly performance data (placeholder)
        monthly_performance = [
            {"month": "Jan", "revenue_growth": 12.5, "sales_growth": 10.2},
            {"month": "Feb", "revenue_growth": 15.8, "sales_growth": 13.5},
            {"month": "Mar", "revenue_growth": 18.2, "sales_growth": 16.1}
        ]

        return PerformanceReportData(
            metrics=metrics,
            kpis=kpis,
            monthly_performance=monthly_performance
        )

    def generate_custom_report(self, config: CustomReportConfig, filters: Optional[ReportFilters] = None) -> CustomReportData:
        """Generate custom report based on configuration."""
        # This would implement a flexible report builder
        # For now, return placeholder data
        data = {
            "selected_metrics": config.selected_metrics,
            "chart_data": [{"name": "Sample", "value": 100}],
            "table_data": [{"column1": "value1", "column2": "value2"}]
        }
        
        charts = [
            {"type": "bar", "data": [1, 2, 3, 4, 5]},
            {"type": "line", "data": [10, 20, 15, 25, 30]}
        ]

        return CustomReportData(
            config=config,
            data=data,
            charts=charts
        )

    def save_report(self, report_type: ReportType, name: str, data: Dict[str, Any], user_id: int) -> Report:
        """Save a generated report to database."""
        report = Report(
            name=name,
            report_type=report_type,
            config={"filters": {}, "generated_data": data},
            status="completed",
            user_id=user_id,
            generated_at=datetime.now()
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report

    def get_report_templates(self, report_type: Optional[ReportType] = None) -> List[ReportTemplate]:
        """Get available report templates."""
        query = self.db.query(ReportTemplate).filter(ReportTemplate.is_active == True)
        
        if report_type:
            query = query.filter(ReportTemplate.report_type == report_type)
        
        return query.all()

    def get_saved_reports(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Report]:
        """Get user's saved reports."""
        return (
            self.db.query(Report)
            .filter(Report.user_id == user_id)
            .order_by(desc(Report.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
