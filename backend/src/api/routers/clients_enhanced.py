"""
Enhanced Clients API Router with Client Assignment Access Control
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.auth_dependencies import (
    get_current_user, require_permissions, require_roles,
    get_user_accessible_clients, require_client_access
)
from ...core.exceptions import AppException, create_http_exception
from ...models.db_models import User, Client, ClientAssignment, UserRole, ClientAssignmentStatus
from ...models.schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientWithUsersResponse,
    UserResponse, MessageResponse
)
from ...services.client_assignment_service import ClientAssignmentService


router = APIRouter(prefix="/clients", tags=["Clients (Enhanced)"])


@router.get(
    "/",
    response_model=List[ClientWithUsersResponse],
    summary="List Clients with Access Control",
    description="Get clients accessible to current user with assignment information"
)
async def list_clients_with_access_control(
    page: int = Query(1, gt=0, description="Page number"),
    per_page: int = Query(10, gt=0, le=100, description="Items per page"),
    include_inactive: bool = Query(False, description="Include inactive clients"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """List clients with access control filtering"""
    try:
        # Build base query
        query = select(Client).options(
            selectinload(Client.client_assignments).selectinload(ClientAssignment.user)
        )
        
        # Apply access control filtering
        if current_user.role != UserRole.SUPER_ADMIN:
            query = query.where(Client.id.in_(accessible_clients))
        
        # Filter by active status
        if not include_inactive:
            query = query.where(Client.is_active == True)
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # Execute query
        result = await db.execute(query)
        clients = result.scalars().all()
        
        # Convert to response format
        response_clients = []
        for client in clients:
            # Count active assignments
            active_assignments = [
                a for a in client.client_assignments 
                if a.status == ClientAssignmentStatus.ACTIVE
            ]
            
            response_client = ClientWithUsersResponse(
                id=client.id,
                name=client.name,
                description=client.description,
                contact_email=client.contact_email,
                is_active=client.is_active,
                created_at=client.created_at,
                updated_at=client.updated_at,
                assigned_users=active_assignments,
                total_assigned_users=len(active_assignments)
            )
            response_clients.append(response_client)
        
        return response_clients
        
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/{client_id}",
    response_model=ClientWithUsersResponse,
    summary="Get Client with Access Control",
    description="Get a specific client with user assignments (access controlled)"
)
async def get_client_with_access_control(
    client_id: int = Path(..., description="Client ID"),
    include_inactive_assignments: bool = Query(False, description="Include inactive assignments"),
    current_user: User = Depends(require_client_access),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific client with access control"""
    try:
        # Get client with assignments
        query = select(Client).where(Client.id == client_id).options(
            selectinload(Client.client_assignments).selectinload(ClientAssignment.user),
            selectinload(Client.client_assignments).selectinload(ClientAssignment.assigned_by)
        )
        
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        # Filter assignments by status if needed
        assignments = client.client_assignments
        if not include_inactive_assignments:
            assignments = [
                a for a in assignments 
                if a.status == ClientAssignmentStatus.ACTIVE
            ]
        
        return ClientWithUsersResponse(
            id=client.id,
            name=client.name,
            description=client.description,
            contact_email=client.contact_email,
            is_active=client.is_active,
            created_at=client.created_at,
            updated_at=client.updated_at,
            assigned_users=assignments,
            total_assigned_users=len(assignments)
        )
        
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Client",
    description="Create a new client (Admin+ only)"
)
@require_permissions(["create_client"])
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new client"""
    try:
        # Check for duplicate name
        query = select(Client).where(Client.name == client_data.name)
        result = await db.execute(query)
        existing_client = result.scalar_one_or_none()
        
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Client with this name already exists"
            )
        
        # Create client
        client = Client(
            name=client_data.name,
            description=client_data.description,
            contact_email=client_data.contact_email
        )
        
        db.add(client)
        await db.commit()
        await db.refresh(client)
        
        return ClientResponse.model_validate(client)
        
    except AppException as e:
        raise create_http_exception(e)


@router.put(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update Client",
    description="Update a client (Admin+ only, with access control)"
)
@require_permissions(["update_client"])
async def update_client(
    client_id: int = Path(..., description="Client ID"),
    client_data: ClientUpdate = ...,
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Update a client"""
    try:
        # Check access for non-super-admins
        if current_user.role != UserRole.SUPER_ADMIN:
            if client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client"
                )
        
        # Get client
        query = select(Client).where(Client.id == client_id)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        # Check for name conflicts if name is being updated
        if client_data.name and client_data.name != client.name:
            query = select(Client).where(Client.name == client_data.name)
            result = await db.execute(query)
            existing_client = result.scalar_one_or_none()
            
            if existing_client:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Client with this name already exists"
                )
        
        # Update fields
        if client_data.name is not None:
            client.name = client_data.name
        if client_data.description is not None:
            client.description = client_data.description
        if client_data.contact_email is not None:
            client.contact_email = client_data.contact_email
        if client_data.is_active is not None:
            client.is_active = client_data.is_active
        
        await db.commit()
        await db.refresh(client)
        
        return ClientResponse.model_validate(client)
        
    except AppException as e:
        raise create_http_exception(e)


@router.delete(
    "/{client_id}",
    response_model=MessageResponse,
    summary="Delete Client",
    description="Delete a client (Super Admin only)"
)
@require_roles([UserRole.SUPER_ADMIN])
async def delete_client(
    client_id: int = Path(..., description="Client ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a client (Super Admin only)"""
    try:
        # Get client
        query = select(Client).where(Client.id == client_id)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        # Check for active assignments
        query = select(func.count(ClientAssignment.id)).where(
            and_(
                ClientAssignment.client_id == client_id,
                ClientAssignment.status == ClientAssignmentStatus.ACTIVE
            )
        )
        result = await db.execute(query)
        active_assignments = result.scalar()
        
        if active_assignments > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete client with {active_assignments} active user assignments"
            )
        
        # Soft delete by setting inactive
        client.is_active = False
        await db.commit()
        
        return MessageResponse(message="Client deactivated successfully")
        
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/{client_id}/users",
    response_model=List[UserResponse],
    summary="Get Client Users",
    description="Get all users assigned to a client"
)
async def get_client_users(
    client_id: int = Path(..., description="Client ID"),
    include_inactive: bool = Query(False, description="Include inactive assignments"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Get all users assigned to a client"""
    try:
        # Check access
        if current_user.role != UserRole.SUPER_ADMIN:
            if client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client"
                )
        
        # Build query
        query = select(User).join(ClientAssignment).where(
            ClientAssignment.client_id == client_id
        )
        
        if not include_inactive:
            query = query.where(ClientAssignment.status == ClientAssignmentStatus.ACTIVE)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
        
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/{client_id}/assign-user/{user_id}",
    response_model=MessageResponse,
    summary="Assign User to Client",
    description="Quick assign a user to a client"
)
@require_permissions(["manage_client_assignments"])
async def assign_user_to_client(
    client_id: int = Path(..., description="Client ID"),
    user_id: int = Path(..., description="User ID"),
    notes: Optional[str] = Query(None, description="Assignment notes"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Quick assign a user to a client"""
    try:
        from ...models.schemas import ClientAssignmentCreate
        
        service = ClientAssignmentService(db)
        assignment_data = ClientAssignmentCreate(
            user_id=user_id,
            client_id=client_id,
            notes=notes
        )
        
        await service.create_assignment(assignment_data, current_user.id)
        return MessageResponse(message="User assigned to client successfully")
        
    except AppException as e:
        raise create_http_exception(e)


@router.delete(
    "/{client_id}/unassign-user/{user_id}",
    response_model=MessageResponse,
    summary="Unassign User from Client",
    description="Remove user assignment from client"
)
@require_permissions(["manage_client_assignments"])
async def unassign_user_from_client(
    client_id: int = Path(..., description="Client ID"),
    user_id: int = Path(..., description="User ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove user assignment from client"""
    try:
        # Find the assignment
        query = select(ClientAssignment).where(
            and_(
                ClientAssignment.client_id == client_id,
                ClientAssignment.user_id == user_id,
                ClientAssignment.status == ClientAssignmentStatus.ACTIVE
            )
        )
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active assignment not found"
            )
        
        service = ClientAssignmentService(db)
        await service.delete_assignment(assignment.id, current_user.id)
        
        return MessageResponse(message="User unassigned from client successfully")
        
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/my/accessible",
    response_model=List[ClientResponse],
    summary="Get My Accessible Clients",
    description="Get all clients accessible to current user"
)
async def get_my_accessible_clients(
    include_inactive: bool = Query(False, description="Include inactive clients"),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Get clients accessible to current user"""
    try:
        if not accessible_clients:
            return []
        
        query = select(Client).where(Client.id.in_(accessible_clients))
        
        if not include_inactive:
            query = query.where(Client.is_active == True)
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        return [ClientResponse.model_validate(client) for client in clients]
        
    except AppException as e:
        raise create_http_exception(e)