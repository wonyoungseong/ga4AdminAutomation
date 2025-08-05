"""
Client Service
Handles client CRUD operations with RBAC integration
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models.db_models import Client, AuditLog, User
from ..models.schemas import ClientCreate, ClientUpdate, ClientResponse
from ..core.exceptions import NotFoundError, ValidationError


class ClientService:
    """Service for managing client operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_client(self, client_data: ClientCreate) -> ClientResponse:
        """Create a new client"""
        
        # Check if client with same name already exists
        stmt = select(Client).where(Client.name == client_data.name)
        existing_client = await self.db.execute(stmt)
        if existing_client.scalar_one_or_none():
            raise ValidationError(f"Client with name '{client_data.name}' already exists")
        
        # Create new client
        client = Client(
            name=client_data.name,
            description=client_data.description,
            contact_email=client_data.contact_email,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)
        
        return ClientResponse.model_validate(client)
    
    async def list_clients(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[ClientResponse]:
        """List clients with pagination and filters"""
        
        stmt = select(Client)
        
        # Apply filters
        if is_active is not None:
            stmt = stmt.where(Client.is_active == is_active)
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Client.created_at.desc())
        
        result = await self.db.execute(stmt)
        clients = result.scalars().all()
        
        return [ClientResponse.model_validate(client) for client in clients]
    
    async def get_client_by_id(self, client_id: int) -> Optional[ClientResponse]:
        """Get client by ID"""
        
        stmt = select(Client).where(Client.id == client_id)
        result = await self.db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            return None
            
        return ClientResponse.model_validate(client)
    
    async def update_client(
        self, 
        client_id: int, 
        client_data: ClientUpdate
    ) -> Optional[ClientResponse]:
        """Update client information"""
        
        # Get existing client
        stmt = select(Client).where(Client.id == client_id)
        result = await self.db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        # Update fields
        update_data = client_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        
        client.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(client)
        
        return ClientResponse.model_validate(client)
    
    async def delete_client(self, client_id: int) -> bool:
        """Delete client (soft delete by setting is_active=False)"""
        
        # Get existing client
        stmt = select(Client).where(Client.id == client_id)
        result = await self.db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            raise NotFoundError(f"Client with ID {client_id} not found")
        
        # Soft delete
        client.is_active = False
        client.updated_at = datetime.utcnow()
        
        await self.db.commit()
        return True
    
    async def get_client_count(self, is_active: Optional[bool] = None) -> int:
        """Get total count of clients"""
        
        stmt = select(func.count(Client.id))
        
        if is_active is not None:
            stmt = stmt.where(Client.is_active == is_active)
        
        result = await self.db.execute(stmt)
        return result.scalar()