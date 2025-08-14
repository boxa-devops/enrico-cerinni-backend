from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.client_service import ClientService
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientFilter,
    ClientDebtUpdate,
    PaginatedClientResponse,
)
from app.schemas.common import ResponseModel
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=ResponseModel)
async def get_clients(
    name: Optional[str] = Query(None, description="Filter by client name"),
    email: Optional[str] = Query(None, description="Filter by email"),
    phone: Optional[str] = Query(None, description="Filter by phone"),
    has_debt: Optional[bool] = Query(None, description="Filter by debt status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all clients with filtering and pagination."""
    filters = ClientFilter(
        name=name, email=email, phone=phone, has_debt=has_debt, page=page, size=size
    )

    client_service = ClientService(db)
    clients, pagination = client_service.get_clients(filters)

    # Convert to response format
    client_responses = []
    for client in clients:
        client_responses.append(
            ClientResponse(
                id=client.id,
                first_name=client.first_name,
                last_name=client.last_name,
                phone=client.phone,
                address=client.address,
                notes=client.notes,
                debt_amount=client.debt_amount,
                is_active=client.is_active,
                created_at=client.created_at.isoformat(),
                updated_at=client.updated_at.isoformat() if client.updated_at else None,
            )
        )

    return ResponseModel(
        success=True,
        data=PaginatedClientResponse(items=client_responses, pagination=pagination),
        message="Clients retrieved successfully",
    )


@router.get("/{client_id}", response_model=ResponseModel)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific client by ID."""
    client_service = ClientService(db)
    client = client_service.get_client(client_id)

    if not client:
        return ResponseModel(success=False, message="Client not found")

    return ResponseModel(
        success=True,
        data=ClientResponse(
            id=client.id,
            first_name=client.first_name,
            last_name=client.last_name,
            phone=client.phone,
            address=client.address,
            notes=client.notes,
            debt_amount=client.debt_amount,
            is_active=client.is_active,
            created_at=client.created_at.isoformat(),
            updated_at=client.updated_at.isoformat() if client.updated_at else None,
        ),
        message="Client retrieved successfully",
    )


@router.post("/", response_model=ResponseModel)
async def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new client."""
    client_service = ClientService(db)
    try:
        client = client_service.create_client(client_data)
        return ResponseModel(
            success=True,
            data=ClientResponse(
                id=client.id,
                first_name=client.first_name,
                last_name=client.last_name,
                phone=client.phone,
                address=client.address,
                notes=client.notes,
                debt_amount=client.debt_amount,
                is_active=client.is_active,
                created_at=client.created_at.isoformat(),
                updated_at=client.updated_at.isoformat() if client.updated_at else None,
            ),
            message="Client created successfully",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.put("/{client_id}", response_model=ResponseModel)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a client."""
    client_service = ClientService(db)
    try:
        client = client_service.update_client(client_id, client_data)
        if not client:
            return ResponseModel(success=False, message="Client not found")

        return ResponseModel(
            success=True,
            data=ClientResponse(
                id=client.id,
                first_name=client.first_name,
                last_name=client.last_name,
                phone=client.phone,
                address=client.address,
                notes=client.notes,
                debt_amount=client.debt_amount,
                is_active=client.is_active,
                created_at=client.created_at.isoformat(),
                updated_at=client.updated_at.isoformat() if client.updated_at else None,
            ),
            message="Client updated successfully",
        )
    except HTTPException as e:
        return ResponseModel(success=False, message=e.detail)


@router.delete("/{client_id}", response_model=ResponseModel)
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a client."""
    client_service = ClientService(db)
    success = client_service.delete_client(client_id)

    if not success:
        return ResponseModel(success=False, message="Client not found")

    return ResponseModel(success=True, message="Client deleted successfully")


@router.patch("/{client_id}/debt", response_model=ResponseModel)
async def update_client_debt(
    client_id: int,
    debt_data: ClientDebtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update client debt amount."""
    client_service = ClientService(db)
    client = client_service.update_client_debt(client_id, debt_data.debt_amount)

    if not client:
        return ResponseModel(success=False, message="Client not found")

    return ResponseModel(
        success=True,
        data=ClientResponse(
            id=client.id,
            first_name=client.first_name,
            last_name=client.last_name,
            phone=client.phone,
            address=client.address,
            notes=client.notes,
            debt_amount=client.debt_amount,
            is_active=client.is_active,
            created_at=client.created_at.isoformat(),
            updated_at=client.updated_at.isoformat() if client.updated_at else None,
        ),
        message="Client debt updated successfully",
    )
