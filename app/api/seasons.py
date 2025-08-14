from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Season
from app.schemas.season import SeasonCreate, SeasonUpdate, SeasonResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.post("", response_model=ResponseModel)
def create_season(
    season: SeasonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new season"""
    try:
        db_season = Season(**season.model_dump())
        db.add(db_season)
        db.commit()
        db.refresh(db_season)
        return ResponseModel(
            success=True,
            message="Season created successfully",
            data=SeasonResponse(
                id=db_season.id,
                name=db_season.name,
                description=db_season.description,
                created_at=db_season.created_at.isoformat(),
                updated_at=db_season.updated_at.isoformat()
                if db_season.updated_at
                else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to create season: {str(e)}")


@router.get("", response_model=ResponseModel)
def get_seasons(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all seasons"""
    try:
        seasons = db.query(Season).offset(skip).limit(limit).all()
        return ResponseModel(
            success=True,
            message="Seasons fetched successfully",
            data=[
                SeasonResponse(
                    id=season.id,
                    name=season.name,
                    description=season.description,
                    created_at=season.created_at.isoformat(),
                    updated_at=season.updated_at.isoformat() if season.updated_at else None,
                )
                for season in seasons
            ],
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch seasons: {str(e)}")


@router.get("/{season_id}", response_model=ResponseModel)
def get_season(
    season_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific season by ID"""
    try:
        season = db.query(Season).filter(Season.id == season_id).first()
        if not season:
            return ResponseModel(success=False, message="Season not found")
        
        return ResponseModel(
            success=True,
            message="Season fetched successfully",
            data=SeasonResponse(
                id=season.id,
                name=season.name,
                description=season.description,
                created_at=season.created_at.isoformat(),
                updated_at=season.updated_at.isoformat() if season.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to fetch season: {str(e)}")


@router.put("/{season_id}", response_model=ResponseModel)
def update_season(
    season_id: int,
    season: SeasonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a season"""
    try:
        db_season = db.query(Season).filter(Season.id == season_id).first()
        if not db_season:
            return ResponseModel(success=False, message="Season not found")

        for field, value in season.model_dump(exclude_unset=True).items():
            setattr(db_season, field, value)

        db.commit()
        db.refresh(db_season)
        return ResponseModel(
            success=True,
            message="Season updated successfully",
            data=SeasonResponse(
                id=db_season.id,
                name=db_season.name,
                description=db_season.description,
                created_at=db_season.created_at.isoformat(),
                updated_at=db_season.updated_at.isoformat() if db_season.updated_at else None,
            ),
        )
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to update season: {str(e)}")


@router.delete("/{season_id}", response_model=ResponseModel)
def delete_season(
    season_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a season"""
    try:
        db_season = db.query(Season).filter(Season.id == season_id).first()
        if not db_season:
            return ResponseModel(success=False, message="Season not found")

        db.delete(db_season)
        db.commit()
        return ResponseModel(success=True, message="Season deleted successfully")
    except Exception as e:
        return ResponseModel(success=False, message=f"Failed to delete season: {str(e)}")
