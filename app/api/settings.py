from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.category import Category
from app.models.product import Product

router = APIRouter(prefix="/settings", tags=["Settings"])


# Category endpoints
@router.get("/categories", response_model=ResponseModel)
async def get_categories(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get all categories."""
    categories = db.query(Category).all()

    category_responses = []
    for category in categories:
        category_responses.append(
            CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                created_at=category.created_at.isoformat(),
                updated_at=category.updated_at.isoformat()
                if category.updated_at
                else None,
            )
        )

    return ResponseModel(
        success=True,
        data=category_responses,
        message="Categories retrieved successfully",
    )


@router.post("/categories", response_model=ResponseModel)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new category."""
    # Check if category with same name already exists
    existing_category = (
        db.query(Category).filter(Category.name == category_data.name).first()
    )
    if existing_category:
        return ResponseModel(
            success=False, message="Category with this name already exists"
        )

    db_category = Category(**category_data.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return ResponseModel(
        success=True,
        data=CategoryResponse(
            id=db_category.id,
            name=db_category.name,
            description=db_category.description,
            created_at=db_category.created_at.isoformat(),
            updated_at=db_category.updated_at.isoformat()
            if db_category.updated_at
            else None,
        ),
        message="Category created successfully",
    )


@router.put("/categories/{category_id}", response_model=ResponseModel)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return ResponseModel(success=False, message="Category not found")

    # Check if name is being updated and if it conflicts
    if category_data.name and category_data.name != category.name:
        existing_category = (
            db.query(Category).filter(Category.name == category_data.name).first()
        )
        if existing_category:
            return ResponseModel(
                success=False, message="Category with this name already exists"
            )

    # Update fields
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return ResponseModel(
        success=True,
        data=CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            created_at=category.created_at.isoformat(),
            updated_at=category.updated_at.isoformat() if category.updated_at else None,
        ),
        message="Category updated successfully",
    )


@router.delete("/categories/{category_id}", response_model=ResponseModel)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return ResponseModel(success=False, message="Category not found")

    # Check if category is being used by products
    products_count = (
        db.query(Product).filter(Product.category_id == category_id).count()
    )
    if products_count > 0:
        return ResponseModel(
            success=False,
            message=f"Cannot delete category. It is used by {products_count} product(s)",
        )

    db.delete(category)
    db.commit()

    return ResponseModel(success=True, message="Category deleted successfully")