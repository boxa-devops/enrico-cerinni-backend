from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Color
from app.schemas.color import ColorCreate, ColorUpdate, ColorResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/colors", tags=["colors"])


@router.post("", response_model=ResponseModel)
def create_color(
    color: ColorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new color"""
    try:
        db_color = Color(**color.dict())
        db.add(db_color)
        db.commit()
        db.refresh(db_color)
        return ResponseModel(
            success=True,
            message="Color created successfully",
            data=ColorResponse(
                id=db_color.id,
                name=db_color.name,
                hex_code=db_color.hex_code,
                description=db_color.description,
                created_at=db_color.created_at.isoformat(),
                updated_at=db_color.updated_at.isoformat() if db_color.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to create color: {str(e)}")


@router.get("", response_model=ResponseModel)
def get_colors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all colors"""
    try:
        colors = db.query(Color).offset(skip).limit(limit).all()
        return ResponseModel(
            success=True,
            message="Colors fetched successfully",
            data=[
                ColorResponse(
                    id=color.id,
                    name=color.name,
                    hex_code=color.hex_code,
                    description=color.description,
                    created_at=color.created_at.isoformat(),
                    updated_at=color.updated_at.isoformat() if color.updated_at else None,
                )
                for color in colors
            ],
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch colors: {str(e)}")


@router.get("/{color_id}", response_model=ResponseModel)
def get_color(
    color_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific color by ID"""
    try:
        color = db.query(Color).filter(Color.id == color_id).first()
        if not color:
            return ResponseModel(success=False, message="Color not found")
        
        return ResponseModel(
            success=True,
            message="Color fetched successfully",
            data=ColorResponse(
                id=color.id,
                name=color.name,
                hex_code=color.hex_code,
                description=color.description,
                created_at=color.created_at.isoformat(),
                updated_at=color.updated_at.isoformat() if color.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch color: {str(e)}")


@router.put("/{color_id}", response_model=ResponseModel)
def update_color(
    color_id: int,
    color: ColorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a color"""
    try:
        db_color = db.query(Color).filter(Color.id == color_id).first()
        if not db_color:
            return ResponseModel(success=False, message="Color not found")

        for field, value in color.dict(exclude_unset=True).items():
            setattr(db_color, field, value)

        db.commit()
        db.refresh(db_color)
        return ResponseModel(
            success=True,
            message="Color updated successfully",
            data=ColorResponse(
                id=db_color.id,
                name=db_color.name,
                hex_code=db_color.hex_code,
                description=db_color.description,
                created_at=db_color.created_at.isoformat(),
                updated_at=db_color.updated_at.isoformat() if db_color.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to update color: {str(e)}")


@router.delete("/{color_id}", response_model=ResponseModel)
def delete_color(
    color_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a color"""
    try:
        db_color = db.query(Color).filter(Color.id == color_id).first()
        if not db_color:
            return ResponseModel(success=False, message="Color not found")

        db.delete(db_color)
        db.commit()
        return ResponseModel(success=True, message="Color deleted successfully")
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to delete color: {str(e)}")
