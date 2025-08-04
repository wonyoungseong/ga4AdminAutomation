"""
Client Assignment API Router
Handles client-user assignment operations with comprehensive access control
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth_dependencies import (
    get_current_user, require_permissions, require_roles, 
    get_user_accessible_clients
)
from ...core.exceptions import AppException, create_http_exception
from ...models.db_models import User, UserRole
from ...models.schemas import (
    ClientAssignmentCreate, ClientAssignmentUpdate, ClientAssignmentBulkCreate,
    ClientAssignmentResponse, UserWithClientsResponse, ClientWithUsersResponse,
    AccessControlSummary, MessageResponse
)
from ...services.client_assignment_service import ClientAssignmentService


router = APIRouter(prefix="/client-assignments", tags=["Client Assignments"])


@router.post(
    "/",
    response_model=ClientAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Client Assignment",
    description="Assign a user to a client with role-based access control"
)
@require_permissions(["manage_client_assignments"])
async def create_client_assignment(
    assignment_data: ClientAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new client assignment"""
    try:
        service = ClientAssignmentService(db)
        return await service.create_assignment(assignment_data, current_user.id)
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/bulk",
    response_model=List[ClientAssignmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Create Client Assignments",
    description="Create multiple client assignments in one operation"
)
@require_permissions(["manage_client_assignments"])
async def bulk_create_client_assignments(
    bulk_data: ClientAssignmentBulkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple client assignments"""
    try:
        service = ClientAssignmentService(db)
        return await service.bulk_create_assignments(bulk_data, current_user.id)
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/",
    response_model=List[ClientAssignmentResponse],
    summary="List Client Assignments",
    description="Get client assignments based on user role and access"
)
async def list_client_assignments(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    status: Optional[str] = Query(None, description="Filter by assignment status"),
    include_inactive: bool = Query(False, description="Include inactive assignments"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """List client assignments with filtering"""
    try:
        service = ClientAssignmentService(db)
        
        # Apply role-based filtering
        if current_user.role == UserRole.SUPER_ADMIN:
            # Super Admins can see all assignments
            pass
        elif current_user.role == UserRole.ADMIN:
            # Admins can see assignments for accessible clients
            if client_id and client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to client assignments"
                )
        else:
            # Regular users can only see their own assignments
            user_id = current_user.id
        
        # Get assignments based on filters
        if user_id:
            assignments = await service.get_user_assignments(user_id, include_inactive)
        elif client_id:
            assignments = await service.get_client_assignments(client_id, include_inactive)
        else:
            # For Super Admins, implement a general listing method if needed
            assignments = []
        
        return assignments
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/{assignment_id}",
    response_model=ClientAssignmentResponse,
    summary="Get Client Assignment",
    description="Get a specific client assignment by ID"
)
async def get_client_assignment(
    assignment_id: int = Path(..., description="Assignment ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific client assignment"""
    try:
        service = ClientAssignmentService(db)
        # Implementation would need to check if user can access this assignment
        # For now, we'll implement basic role checking
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # This would need implementation in the service
        # For now, return a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Get specific assignment not implemented yet"
        )
    except AppException as e:
        raise create_http_exception(e)


@router.put(
    "/{assignment_id}",
    response_model=ClientAssignmentResponse,
    summary="Update Client Assignment",
    description="Update a client assignment"
)
@require_permissions(["manage_client_assignments"])
async def update_client_assignment(
    assignment_id: int = Path(..., description="Assignment ID"),
    update_data: ClientAssignmentUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a client assignment"""
    try:
        service = ClientAssignmentService(db)
        return await service.update_assignment(assignment_id, update_data, current_user.id)
    except AppException as e:
        raise create_http_exception(e)


@router.delete(
    "/{assignment_id}",
    response_model=MessageResponse,
    summary="Delete Client Assignment",
    description="Remove a client assignment"
)
@require_permissions(["manage_client_assignments"])
async def delete_client_assignment(
    assignment_id: int = Path(..., description="Assignment ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a client assignment"""
    try:
        service = ClientAssignmentService(db)
        await service.delete_assignment(assignment_id, current_user.id)
        return MessageResponse(message="Client assignment deleted successfully")
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/users/{user_id}/clients",
    response_model=List[ClientAssignmentResponse],
    summary="Get User's Client Assignments",
    description="Get all client assignments for a specific user"
)
async def get_user_client_assignments(
    user_id: int = Path(..., description="User ID"),
    include_inactive: bool = Query(False, description="Include inactive assignments"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all client assignments for a user"""
    try:
        # Check if user can access this information
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            if current_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to user assignments"
                )
        
        service = ClientAssignmentService(db)
        return await service.get_user_assignments(user_id, include_inactive)
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/clients/{client_id}/users",
    response_model=List[ClientAssignmentResponse],
    summary="Get Client's User Assignments",
    description="Get all user assignments for a specific client"
)
async def get_client_user_assignments(
    client_id: int = Path(..., description="Client ID"),
    include_inactive: bool = Query(False, description="Include inactive assignments"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Get all user assignments for a client"""
    try:
        # Check client access
        if current_user.role != UserRole.SUPER_ADMIN:
            if client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to client assignments"
                )
        
        service = ClientAssignmentService(db)
        return await service.get_client_assignments(client_id, include_inactive)
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/access-control/{user_id}",
    response_model=AccessControlSummary,
    summary="Get User Access Control Summary",
    description="Get comprehensive access control information for a user"
)
@require_roles([UserRole.SUPER_ADMIN, UserRole.ADMIN])
async def get_user_access_control_summary(
    user_id: int = Path(..., description="User ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get access control summary for a user"""
    try:
        # Get user to determine their role
        from sqlalchemy import select
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        service = ClientAssignmentService(db)
        return await service.get_access_control_summary(user_id, target_user.role)
        
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/validate-access/{client_id}",
    response_model=dict,
    summary="Validate Client Access",
    description="Check if current user has access to a specific client"
)
async def validate_client_access(
    client_id: int = Path(..., description="Client ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate if user has access to a client"""
    try:
        service = ClientAssignmentService(db)
        has_access = await service.check_user_client_access(
            user_id=current_user.id,
            client_id=client_id,
            user_role=current_user.role
        )
        
        return {
            "user_id": current_user.id,
            "client_id": client_id,
            "has_access": has_access,
            "role": current_user.role.value
        }
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/my/accessible-clients",
    response_model=List[int],
    summary="Get My Accessible Clients",
    description="Get list of client IDs accessible to current user"
)
async def get_my_accessible_clients(
    accessible_clients: List[int] = Depends(get_user_accessible_clients)
):
    """Get accessible clients for current user"""
    return accessible_clients