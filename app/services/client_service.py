from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple
from decimal import Decimal
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate, ClientFilter
from app.utils.helpers import paginate_query, calculate_pagination_info
from fastapi import HTTPException, status


class ClientService:
    def __init__(self, db: Session):
        self.db = db

    def create_client(self, client_data: ClientCreate) -> Client:
        """Create a new client."""
        # Check if client with same email already exists
        if client_data.phone:
            existing_client = (
                self.db.query(Client).filter(Client.phone == client_data.phone).first()
            )
            if existing_client:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client with this phone already exists",
                )

        db_client = Client(**client_data.model_dump())
        self.db.add(db_client)
        self.db.commit()
        self.db.refresh(db_client)
        return db_client

    def get_client(self, client_id: int) -> Optional[Client]:
        """Get a client by ID."""
        return self.db.query(Client).filter(Client.id == client_id).first()

    def get_clients(self, filters: ClientFilter) -> Tuple[List[Client], dict]:
        """Get clients with filtering and pagination."""
        query = self.db.query(Client)

        # Apply filters
        if filters.name:
            query = query.filter(
                or_(
                    Client.first_name.ilike(f"%{filters.name}%"),
                    Client.last_name.ilike(f"%{filters.name}%"),
                )
            )

        if filters.phone:
            query = query.filter(Client.phone.ilike(f"%{filters.phone}%"))

        if filters.has_debt is not None:
            if filters.has_debt:
                query = query.filter(Client.debt_amount > 0)
            else:
                query = query.filter(Client.debt_amount == 0)

        total = query.count()

        query = paginate_query(query, filters.page, filters.size)

        clients = query.all()

        # Calculate pagination info
        pagination = calculate_pagination_info(total, filters.page, filters.size)

        return clients, pagination

    def update_client(
        self, client_id: int, client_data: ClientUpdate
    ) -> Optional[Client]:
        """Update a client."""
        client = self.get_client(client_id)
        if not client:
            return None

        # Check if email is being updated and if it conflicts
        if client_data.phone and client_data.phone != client.phone:
            existing_client = (
                self.db.query(Client).filter(Client.phone == client_data.phone).first()
            )
            if existing_client:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client with this phone already exists",
                )

        # Update fields
        update_data = client_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)

        self.db.commit()
        self.db.refresh(client)
        return client

    def delete_client(self, client_id: int) -> bool:
        """Delete a client."""
        client = self.get_client(client_id)
        if not client:
            return False

        self.db.delete(client)
        self.db.commit()
        return True

    def update_client_debt(
        self, client_id: int, debt_amount: Decimal
    ) -> Optional[Client]:
        """Update client debt amount."""
        client = self.get_client(client_id)
        if not client:
            return None

        client.debt_amount = debt_amount
        self.db.commit()
        self.db.refresh(client)
        return client

    def search_clients(
        self, search_term: str, page: int = 1, size: int = 10
    ) -> Tuple[List[Client], dict]:
        """Search clients by name, email, or phone."""
        query = self.db.query(Client).filter(
            or_(
                Client.first_name.ilike(f"%{search_term}%"),
                Client.last_name.ilike(f"%{search_term}%"),
                Client.email.ilike(f"%{search_term}%"),
                Client.phone.ilike(f"%{search_term}%"),
            )
        )

        total = query.count()
        query = paginate_query(query, page, size)
        clients = query.all()

        pagination = calculate_pagination_info(total, page, size)
        return clients, pagination

    def get_clients_with_debt(self) -> List[Client]:
        """Get all clients with outstanding debt."""
        return self.db.query(Client).filter(Client.debt_amount > 0).all()
