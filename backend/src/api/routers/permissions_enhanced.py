"""
Enhanced Permissions API Router with Client Access Control
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.auth_dependencies import (
    get_current_user, require_permissions, require_roles,
    get_user_accessible_clients
)
from ...core.exceptions import AppException, create_http_exception
from ...models.db_models import (
    User, Client, PermissionGrant, UserRole, 
    PermissionStatus, PermissionLevel
)
from ...models.schemas import (
    PermissionGrantCreate, PermissionGrantUpdate, PermissionGrantResponse,
    MessageResponse
)


router = APIRouter(prefix="/permissions", tags=["Permissions (Enhanced)"])


@router.get(
    "/",
    response_model=List[PermissionGrantResponse],
    summary="List Permission Grants with Access Control",
    description="Get permission grants filtered by user access rights"
)
async def list_permission_grants_with_access_control(
    page: int = Query(1, gt=0, description="Page number"),
    per_page: int = Query(20, gt=0, le=100, description="Items per page"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[PermissionStatus] = Query(None, description="Filter by status"),
    permission_level: Optional[PermissionLevel] = Query(None, description="Filter by permission level"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """List permission grants with access control"""
    try:
        # Build base query with joins
        query = select(PermissionGrant).options(
            selectinload(PermissionGrant.user),
            selectinload(PermissionGrant.client),
            selectinload(PermissionGrant.approved_by)
        )
        
        # Apply role-based access control
        if current_user.role == UserRole.SUPER_ADMIN:
            # Super Admins can see all permission grants
            pass
        elif current_user.role == UserRole.ADMIN:
            # Admins can see permission grants for accessible clients
            query = query.where(PermissionGrant.client_id.in_(accessible_clients))
        else:
            # Regular users can only see their own permission grants
            query = query.where(PermissionGrant.user_id == current_user.id)
        
        # Apply filters
        if client_id:
            # Check if user has access to this client
            if current_user.role != UserRole.SUPER_ADMIN and client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client's permissions"
                )
            query = query.where(PermissionGrant.client_id == client_id)
        
        if user_id:
            # Non-admin users can only filter by their own user_id
            if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                if user_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to other users' permissions"
                    )
            query = query.where(PermissionGrant.user_id == user_id)
        
        if status:
            query = query.where(PermissionGrant.status == status)
        
        if permission_level:
            query = query.where(PermissionGrant.permission_level == permission_level)
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # Order by created_at descending
        query = query.order_by(PermissionGrant.created_at.desc())
        
        # Execute query
        result = await db.execute(query)
        permissions = result.scalars().all()
        
        return [PermissionGrantResponse.model_validate(perm) for perm in permissions]
        
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/{permission_id}",
    response_model=PermissionGrantResponse,
    summary="Get Permission Grant",
    description="Get a specific permission grant with access control"
)
async def get_permission_grant(
    permission_id: int = Path(..., description="Permission Grant ID"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific permission grant"""
    try:
        # Get permission with relationships
        query = select(PermissionGrant).where(PermissionGrant.id == permission_id).options(
            selectinload(PermissionGrant.user),
            selectinload(PermissionGrant.client),
            selectinload(PermissionGrant.approved_by)
        )
        
        result = await db.execute(query)
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission grant not found"
            )
        
        # Check access rights
        if current_user.role == UserRole.SUPER_ADMIN:
            # Super Admins can access any permission
            pass
        elif current_user.role == UserRole.ADMIN:
            # Admins can access permissions for their accessible clients
            if permission.client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this permission grant"
                )
        else:
            # Regular users can only access their own permissions
            if permission.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this permission grant"
                )
        
        return PermissionGrantResponse.model_validate(permission)
        
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/",
    response_model=PermissionGrantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Permission Grant Request",
    description="Create a new permission grant request with client access validation"
)
@require_permissions(["create_permission"])
async def create_permission_grant(
    permission_data: PermissionGrantCreate,
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Create a new permission grant request"""
    try:
        # Check if client is accessible
        if current_user.role != UserRole.SUPER_ADMIN:
            if permission_data.client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this client"
                )
        
        # Validate that user, client, and service account exist
        user_query = select(User).where(User.id == current_user.id)
        client_query = select(Client).where(Client.id == permission_data.client_id)
        
        user_result = await db.execute(user_query)
        client_result = await db.execute(client_query)
        
        user = user_result.scalar_one_or_none()
        client = client_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        if not client:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
        
        # Check for existing active permission grant
        existing_query = select(PermissionGrant).where(
            and_(
                PermissionGrant.user_id == current_user.id,
                PermissionGrant.client_id == permission_data.client_id,
                PermissionGrant.ga_property_id == permission_data.ga_property_id,
                PermissionGrant.target_email == permission_data.target_email,
                PermissionGrant.status.in_([PermissionStatus.PENDING, PermissionStatus.APPROVED])
            )
        )
        
        existing_result = await db.execute(existing_query)
        existing_permission = existing_result.scalar_one_or_none()
        
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission grant already exists for this property and email"
            )
        
        # Create permission grant
        permission = PermissionGrant(
            user_id=current_user.id,
            client_id=permission_data.client_id,
            service_account_id=permission_data.service_account_id,
            ga_property_id=permission_data.ga_property_id,
            target_email=permission_data.target_email,
            permission_level=permission_data.permission_level,
            reason=permission_data.reason,
            expires_at=permission_data.expires_at
        )
        
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        
        # Load relationships
        await db.refresh(permission, ["user", "client"])
        
        return PermissionGrantResponse.model_validate(permission)
        
    except AppException as e:
        raise create_http_exception(e)


@router.put(
    "/{permission_id}",
    response_model=PermissionGrantResponse,
    summary="Update Permission Grant",
    description="Update a permission grant (approve/reject/modify)"
)
async def update_permission_grant(
    permission_id: int = Path(..., description="Permission Grant ID"),
    update_data: PermissionGrantUpdate = ...,
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Update a permission grant"""
    try:
        # Get permission grant
        query = select(PermissionGrant).where(PermissionGrant.id == permission_id).options(
            selectinload(PermissionGrant.user),
            selectinload(PermissionGrant.client)
        )
        
        result = await db.execute(query)
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission grant not found"
            )
        
        # Check access rights for updates
        can_update = False
        
        if current_user.role == UserRole.SUPER_ADMIN:
            can_update = True
        elif current_user.role == UserRole.ADMIN:
            # Admins can update permissions for accessible clients
            if permission.client_id in accessible_clients:
                can_update = True
        else:
            # Regular users can only update their own pending permissions (limited fields)
            if permission.user_id == current_user.id and permission.status == PermissionStatus.PENDING:
                # Only allow updating reason and notes for own permissions
                if update_data.status or update_data.permission_level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cannot modify status or permission level"
                    )
                can_update = True
        
        if not can_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this permission grant"
            )
        
        # Apply updates
        if update_data.permission_level is not None:
            permission.permission_level = update_data.permission_level
        
        if update_data.status is not None:
            # Only admins+ can change status
            if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify permission status"
                )
            
            permission.status = update_data.status
            
            if update_data.status == PermissionStatus.APPROVED:
                permission.approved_at = db.func.now()
                permission.approved_by_id = current_user.id
            elif update_data.status in [PermissionStatus.REJECTED, PermissionStatus.REVOKED]:
                permission.approved_at = None
                permission.approved_by_id = None
        
        if update_data.expires_at is not None:
            permission.expires_at = update_data.expires_at
        
        if update_data.notes is not None:
            permission.notes = update_data.notes
        
        await db.commit()
        await db.refresh(permission)
        
        # Load relationships
        await db.refresh(permission, ["user", "client", "approved_by"])
        
        return PermissionGrantResponse.model_validate(permission)
        
    except AppException as e:
        raise create_http_exception(e)


@router.delete(
    "/{permission_id}",
    response_model=MessageResponse,
    summary="Delete Permission Grant",
    description="Delete a permission grant"
)
@require_permissions(["delete_permission"])
async def delete_permission_grant(
    permission_id: int = Path(..., description="Permission Grant ID"),
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Delete a permission grant"""
    try:
        # Get permission grant
        query = select(PermissionGrant).where(PermissionGrant.id == permission_id)
        result = await db.execute(query)
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission grant not found"
            )
        
        # Check access rights
        if current_user.role == UserRole.SUPER_ADMIN:
            # Super Admins can delete any permission
            pass
        elif current_user.role == UserRole.ADMIN:
            # Admins can delete permissions for accessible clients
            if permission.client_id not in accessible_clients:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to delete this permission grant"
                )
        else:
            # Regular users can only delete their own pending permissions
            if permission.user_id != current_user.id or permission.status != PermissionStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only delete your own pending permission grants"
                )
        
        await db.delete(permission)
        await db.commit()
        
        return MessageResponse(message="Permission grant deleted successfully")
        
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/my/requests",
    response_model=List[PermissionGrantResponse],
    summary="Get My Permission Requests",
    description="Get current user's permission requests"
)
async def get_my_permission_requests(
    status: Optional[PermissionStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's permission requests"""
    try:
        query = select(PermissionGrant).where(
            PermissionGrant.user_id == current_user.id
        ).options(
            selectinload(PermissionGrant.client),
            selectinload(PermissionGrant.approved_by)
        )
        
        if status:
            query = query.where(PermissionGrant.status == status)
        
        query = query.order_by(PermissionGrant.created_at.desc())
        
        result = await db.execute(query)
        permissions = result.scalars().all()
        
        return [PermissionGrantResponse.model_validate(perm) for perm in permissions]
        
    except AppException as e:
        raise create_http_exception(e)


@router.get(
    "/pending/review",
    response_model=List[PermissionGrantResponse],
    summary="Get Pending Permissions for Review",
    description="Get pending permission requests that current user can approve"
)
@require_roles([UserRole.SUPER_ADMIN, UserRole.ADMIN])
async def get_pending_permissions_for_review(
    current_user: User = Depends(get_current_user),
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    db: AsyncSession = Depends(get_db)
):
    """Get pending permission requests for review"""
    try:
        query = select(PermissionGrant).where(
            PermissionGrant.status == PermissionStatus.PENDING
        ).options(
            selectinload(PermissionGrant.user),
            selectinload(PermissionGrant.client)
        )
        
        # Apply access control for Admins
        if current_user.role == UserRole.ADMIN:
            query = query.where(PermissionGrant.client_id.in_(accessible_clients))
        
        query = query.order_by(PermissionGrant.created_at.asc())
        
        result = await db.execute(query)
        permissions = result.scalars().all()
        
        return [PermissionGrantResponse.model_validate(perm) for perm in permissions]
        
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/{permission_id}/approve",
    response_model=PermissionGrantResponse,
    summary="Approve Permission Grant",
    description="Approve a pending permission grant"
)
@require_permissions(["approve_permission"])
async def approve_permission_grant(
    permission_id: int = Path(..., description="Permission Grant ID"),
    notes: Optional[str] = Query(None, description="Approval notes"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a permission grant"""
    try:
        update_data = PermissionGrantUpdate(
            status=PermissionStatus.APPROVED,
            notes=notes
        )
        
        return await update_permission_grant(
            permission_id=permission_id,
            update_data=update_data,
            current_user=current_user,
            accessible_clients=await get_user_accessible_clients(current_user, db),
            db=db
        )
        
    except AppException as e:
        raise create_http_exception(e)


@router.post(
    "/{permission_id}/reject",
    response_model=PermissionGrantResponse,
    summary="Reject Permission Grant",
    description="Reject a pending permission grant"
)
@require_permissions(["reject_permission"])
async def reject_permission_grant(
    permission_id: int = Path(..., description="Permission Grant ID"),
    reason: str = Query(..., description="Rejection reason"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a permission grant"""
    try:
        update_data = PermissionGrantUpdate(
            status=PermissionStatus.REJECTED,
            notes=reason
        )
        
        return await update_permission_grant(
            permission_id=permission_id,
            update_data=update_data,
            current_user=current_user,
            accessible_clients=await get_user_accessible_clients(current_user, db),
            db=db
        )
        
    except AppException as e:
        raise create_http_exception(e)