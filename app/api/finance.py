from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.common import ResponseModel
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.schemas.salary_payment import SalaryPaymentCreate, SalaryPaymentUpdate, SalaryPaymentResponse
from app.models import Expense, Employee, Supplier, SalaryPayment

router = APIRouter(prefix="/finance", tags=["Finance"])

# ==================== EXPENSES ====================


@router.get("/expenses", response_model=ResponseModel)
async def get_expenses(
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.utils.helpers import paginate_query, calculate_pagination_info
    
    query = db.query(Expense)

    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    total = query.count()
    query = query.order_by(Expense.date.desc())
    expenses = paginate_query(query, page, size).all()
    pagination = calculate_pagination_info(total, page, size)

    return ResponseModel(
        success=True,
        data={
            "items": [ExpenseResponse.from_orm(expense) for expense in expenses],
            "pagination": pagination,
        },
        message="Expenses retrieved successfully",
    )


@router.get("/expenses/category/{category}", response_model=ResponseModel)
async def get_expenses_by_category(
    category: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Expense).filter(Expense.category == category)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    total = query.count()
    expenses = query.offset(offset).limit(limit).all()

    return ResponseModel(
        success=True,
        data={
            "items": [ExpenseResponse.from_orm(expense) for expense in expenses],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        message=f"Expenses for category '{category}' retrieved successfully",
    )


@router.post("/expenses", response_model=ResponseModel)
async def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    expense = Expense(**expense_data.dict())
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return ResponseModel(
        success=True,
        data=ExpenseResponse.from_orm(expense),
        message="Expense created successfully",
    )


@router.put("/expenses/{expense_id}", response_model=ResponseModel)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for field, value in expense_data.dict(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)

    return ResponseModel(
        success=True,
        data=ExpenseResponse.from_orm(expense),
        message="Expense updated successfully",
    )


@router.delete("/expenses/{expense_id}", response_model=ResponseModel)
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()

    return ResponseModel(success=True, message="Expense deleted successfully")


@router.get("/expenses/stats", response_model=ResponseModel)
async def get_expense_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Expense)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    expenses = query.all()

    total_expenses = sum(expense.amount for expense in expenses)
    by_category = {}
    for expense in expenses:
        if expense.category not in by_category:
            by_category[expense.category] = Decimal("0")
        by_category[expense.category] += expense.amount

    return ResponseModel(
        success=True,
        data={
            "total_expenses": total_expenses,
            "by_category": by_category,
            "count": len(expenses),
        },
        message="Expense statistics retrieved successfully",
    )



# ==================== EMPLOYEES ====================


@router.get("/employees", response_model=ResponseModel)
async def get_employees(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.utils.helpers import paginate_query, calculate_pagination_info
    
    query = db.query(Employee)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Employee.name.ilike(search_term))
            | (Employee.position.ilike(search_term))
            | (Employee.email.ilike(search_term))
        )

    total = query.count()
    query = query.order_by(Employee.name.asc())
    employees = paginate_query(query, page, size).all()
    pagination = calculate_pagination_info(total, page, size)

    return ResponseModel(
        success=True,
        data={
            "items": [EmployeeResponse.from_orm(employee) for employee in employees],
            "pagination": pagination,
        },
        message="Employees retrieved successfully",
    )


@router.post("/employees", response_model=ResponseModel)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = Employee(**employee_data.dict())
    db.add(employee)
    db.commit()
    db.refresh(employee)

    return ResponseModel(
        success=True,
        data=EmployeeResponse.model_validate(employee),
        message="Employee created successfully",
    )


@router.put("/employees/{employee_id}", response_model=ResponseModel)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in employee_data.dict(exclude_unset=True).items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return ResponseModel(
        success=True,
        data=EmployeeResponse.from_orm(employee),
        message="Employee updated successfully",
    )


@router.delete("/employees/{employee_id}", response_model=ResponseModel)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()

    return ResponseModel(success=True, message="Employee deleted successfully")


# ==================== SUPPLIERS ====================


@router.get("/suppliers", response_model=ResponseModel)
async def get_suppliers(
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Supplier)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Supplier.name.ilike(search_term))
            | (Supplier.contact_person.ilike(search_term))
            | (Supplier.email.ilike(search_term))
        )

    total = query.count()
    suppliers = query.offset(offset).limit(limit).all()

    return ResponseModel(
        success=True,
        data={
            "items": [SupplierResponse.from_orm(supplier) for supplier in suppliers],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        message="Suppliers retrieved successfully",
    )


@router.post("/suppliers", response_model=ResponseModel)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    supplier = Supplier(**supplier_data.dict())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return ResponseModel(
        success=True,
        data=SupplierResponse.from_orm(supplier),
        message="Supplier created successfully",
    )


@router.put("/suppliers/{supplier_id}", response_model=ResponseModel)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for field, value in supplier_data.dict(exclude_unset=True).items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    return ResponseModel(
        success=True,
        data=SupplierResponse.from_orm(supplier),
        message="Supplier updated successfully",
    )


@router.delete("/suppliers/{supplier_id}", response_model=ResponseModel)
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(supplier)
    db.commit()

    return ResponseModel(success=True, message="Supplier deleted successfully")


# ==================== SALARY PAYMENTS ====================


@router.get("/salary-payments", response_model=ResponseModel)
async def get_salary_payments(
    employee_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(SalaryPayment).join(Employee)

    if employee_id:
        query = query.filter(SalaryPayment.employee_id == employee_id)
    if start_date:
        query = query.filter(SalaryPayment.payment_date >= start_date)
    if end_date:
        query = query.filter(SalaryPayment.payment_date <= end_date)

    total = query.count()
    salary_payments = query.offset(offset).limit(limit).all()

    # Add employee name to response
    result_items = []
    for payment in salary_payments:
        payment_dict = SalaryPaymentResponse.from_orm(payment).dict()
        payment_dict["employee_name"] = payment.employee.name if payment.employee else None
        result_items.append(payment_dict)

    return ResponseModel(
        success=True,
        data={
            "items": result_items,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        message="Salary payments retrieved successfully",
    )


@router.post("/salary-payments", response_model=ResponseModel)
async def create_salary_payment(
    payment_data: SalaryPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == payment_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    salary_payment = SalaryPayment(**payment_data.dict())
    db.add(salary_payment)
    db.commit()
    db.refresh(salary_payment)

    # Add employee name to response
    response_dict = SalaryPaymentResponse.from_orm(salary_payment).dict()
    response_dict["employee_name"] = employee.name

    return ResponseModel(
        success=True,
        data=response_dict,
        message="Salary payment created successfully",
    )


@router.put("/salary-payments/{payment_id}", response_model=ResponseModel)
async def update_salary_payment(
    payment_id: int,
    payment_data: SalaryPaymentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    salary_payment = db.query(SalaryPayment).filter(SalaryPayment.id == payment_id).first()
    if not salary_payment:
        raise HTTPException(status_code=404, detail="Salary payment not found")

    # Check if employee exists when updating employee_id
    if payment_data.employee_id:
        employee = db.query(Employee).filter(Employee.id == payment_data.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in payment_data.dict(exclude_unset=True).items():
        setattr(salary_payment, field, value)

    db.commit()
    db.refresh(salary_payment)

    # Add employee name to response
    response_dict = SalaryPaymentResponse.from_orm(salary_payment).dict()
    response_dict["employee_name"] = salary_payment.employee.name if salary_payment.employee else None

    return ResponseModel(
        success=True,
        data=response_dict,
        message="Salary payment updated successfully",
    )


@router.delete("/salary-payments/{payment_id}", response_model=ResponseModel)
async def delete_salary_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    salary_payment = db.query(SalaryPayment).filter(SalaryPayment.id == payment_id).first()
    if not salary_payment:
        raise HTTPException(status_code=404, detail="Salary payment not found")

    db.delete(salary_payment)
    db.commit()

    return ResponseModel(success=True, message="Salary payment deleted successfully")