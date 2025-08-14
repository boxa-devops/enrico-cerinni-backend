from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Size
from app.schemas.size import SizeCreate, SizeUpdate, SizeResponse
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/sizes", tags=["sizes"])


@router.get("", response_model=ResponseModel)
async def get_sizes(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get all sizes."""
    try:
        sizes = db.query(Size).all()
        return ResponseModel(
            success=True,
            message="Sizes retrieved successfully",
            data=[
                SizeResponse(
                    id=size.id,
                    name=size.name,
                    description=size.description,
                    created_at=size.created_at.isoformat(),
                    updated_at=size.updated_at.isoformat() if size.updated_at else None,
                )
                for size in sizes
            ],
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch sizes: {str(e)}")


@router.post("", response_model=ResponseModel)
async def create_size(
    size_data: SizeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new size."""
    try:
        # Check if size already exists
        existing_size = db.query(Size).filter(Size.name == size_data.name).first()
        if existing_size:
            return ResponseModel(success=False, message="Size with this name already exists")

        size = Size(**size_data.dict())
        db.add(size)
        db.commit()
        db.refresh(size)

        return ResponseModel(
            success=True,
            data=SizeResponse(
                id=size.id,
                name=size.name,
                description=size.description,
                created_at=size.created_at.isoformat(),
                updated_at=size.updated_at.isoformat() if size.updated_at else None,
            ),
            message="Size created successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to create size: {str(e)}")


@router.get("/{size_id}", response_model=ResponseModel)
async def get_size(
    size_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific size."""
    try:
        size = db.query(Size).filter(Size.id == size_id).first()
        if not size:
            return ResponseModel(success=False, message="Size not found")

        return ResponseModel(
            success=True,
            data=SizeResponse(
                id=size.id,
                name=size.name,
                description=size.description,
                created_at=size.created_at.isoformat(),
                updated_at=size.updated_at.isoformat() if size.updated_at else None,
            ),
            message="Size retrieved successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch size: {str(e)}")


@router.put("/{size_id}", response_model=ResponseModel)
async def update_size(
    size_id: int,
    size_data: SizeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a size."""
    try:
        size = db.query(Size).filter(Size.id == size_id).first()
        if not size:
            return ResponseModel(success=False, message="Size not found")

        # Check if new name already exists
        if size_data.name and size_data.name != size.name:
            existing_size = db.query(Size).filter(Size.name == size_data.name).first()
            if existing_size:
                return ResponseModel(success=False, message="Size with this name already exists")

        for field, value in size_data.dict(exclude_unset=True).items():
            setattr(size, field, value)

        db.commit()
        db.refresh(size)

        return ResponseModel(
            success=True,
            data=SizeResponse(
                id=size.id,
                name=size.name,
                description=size.description,
                created_at=size.created_at.isoformat(),
                updated_at=size.updated_at.isoformat() if size.updated_at else None,
            ),
            message="Size updated successfully",
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to update size: {str(e)}")


@router.delete("/{size_id}", response_model=ResponseModel)
async def delete_size(
    size_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a size."""
    try:
        size = db.query(Size).filter(Size.id == size_id).first()
        if not size:
            return ResponseModel(success=False, message="Size not found")

        db.delete(size)
        db.commit()

        return ResponseModel(success=True, message="Size deleted successfully")
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to delete size: {str(e)}")
