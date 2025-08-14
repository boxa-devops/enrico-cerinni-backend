from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Brand
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=ResponseModel)
def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new brand"""
    try:
        db_brand = Brand(**brand.dict())
        db.add(db_brand)
        db.commit()
        db.refresh(db_brand)
        return ResponseModel(
            success=True,
            message="Brand created successfully",
            data=BrandResponse(
                id=db_brand.id,
                name=db_brand.name,
                description=db_brand.description,
                logo_url=db_brand.logo_url,
                created_at=db_brand.created_at.isoformat(),
                updated_at=db_brand.updated_at.isoformat() if db_brand.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to create brand: {str(e)}")


@router.get("", response_model=ResponseModel)
def get_brands(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all brands"""
    try:
        brands = db.query(Brand).offset(skip).limit(limit).all()
        return ResponseModel(
            success=True,
            message="Brands fetched successfully",
            data=[
                BrandResponse(
                    id=brand.id,
                    name=brand.name,
                    description=brand.description,
                    logo_url=brand.logo_url,
                    created_at=brand.created_at.isoformat(),
                    updated_at=brand.updated_at.isoformat() if brand.updated_at else None,
                )
                for brand in brands
            ],
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch brands: {str(e)}")


@router.get("/{brand_id}", response_model=ResponseModel)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific brand by ID"""
    try:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return ResponseModel(success=False, message="Brand not found")
        
        return ResponseModel(
            success=True,
            message="Brand fetched successfully",
            data=BrandResponse(
                id=brand.id,
                name=brand.name,
                description=brand.description,
                logo_url=brand.logo_url,
                created_at=brand.created_at.isoformat(),
                updated_at=brand.updated_at.isoformat() if brand.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch brand: {str(e)}")


@router.put("/{brand_id}", response_model=ResponseModel)
def update_brand(
    brand_id: int,
    brand: BrandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a brand"""
    try:
        db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not db_brand:
            return ResponseModel(success=False, message="Brand not found")

        for field, value in brand.dict(exclude_unset=True).items():
            setattr(db_brand, field, value)

        db.commit()
        db.refresh(db_brand)
        return ResponseModel(
            success=True,
            message="Brand updated successfully",
            data=BrandResponse(
                id=db_brand.id,
                name=db_brand.name,
                description=db_brand.description,
                logo_url=db_brand.logo_url,
                created_at=db_brand.created_at.isoformat(),
                updated_at=db_brand.updated_at.isoformat() if db_brand.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to update brand: {str(e)}")


@router.delete("/{brand_id}", response_model=ResponseModel)
def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a brand"""
    try:
        db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not db_brand:
            return ResponseModel(success=False, message="Brand not found")

        db.delete(db_brand)
        db.commit()
        return ResponseModel(success=True, message="Brand deleted successfully")
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to delete brand: {str(e)}")
