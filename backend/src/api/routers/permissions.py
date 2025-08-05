"""
Permissions API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional, List
from datetime import datetime

from ...core.database import get_db
from ...core.exceptions import NotFoundError, ValidationError, AuthorizationError, GoogleAPIError
from ...models.schemas import (
    PermissionGrantResponse, PermissionGrantCreate, PermissionGrantUpdate, MessageResponse
)
from ...models.db_models import PermissionStatus
from ...core.rbac import Permission, require_permission, get_current_user_with_permissions
from ...services.permission_service import PermissionService

router = APIRouter()


@router.post("/", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_CREATE)
async def create_permission_request(
    grant_data: PermissionGrantCreate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Create a new permission request"""
    try:
        permission_service = PermissionService(db)
        grant = await permission_service.create_permission_request(
            user_id=current_user["user_id"],
            grant_data=grant_data
        )
        return grant
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.get("/", response_model=List[PermissionGrantResponse])
@require_permission(Permission.PERMISSION_READ)
async def list_permission_grants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status_filter: Optional[PermissionStatus] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """List permission grants"""
    permission_service = PermissionService(db)
    
    # Regular users can only see their own grants based on resource ownership
    if current_user.get("resource_ownership") == "self_only":
        user_id = current_user["user_id"]
    
    grants = await permission_service.list_permission_grants(
        skip=skip,
        limit=limit,
        user_id=user_id,
        client_id=client_id,
        status=status_filter
    )
    return grants


@router.get("/{grant_id}", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_READ, resource_ownership=True, allow_self_access=True)
async def get_permission_grant(
    grant_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get permission grant by ID"""
    permission_service = PermissionService(db)
    grant = await permission_service.get_permission_grant(grant_id)
    
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission grant not found"
        )
    
    # RBAC decorator handles access control
    
    return grant


@router.put("/{grant_id}", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_UPDATE)
async def update_permission_grant(
    grant_id: int,
    grant_data: PermissionGrantUpdate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Update permission grant"""
    # RBAC decorator handles access control
    
    # TODO: Implement update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update functionality not yet implemented"
    )


@router.post("/{grant_id}/approve", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_APPROVE)
async def approve_permission_grant(
    grant_id: int,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Approve permission grant"""
    try:
        permission_service = PermissionService(db)
        grant = await permission_service.approve_permission_request(
            grant_id=grant_id,
            approver_id=current_user["user_id"],
            notes=notes
        )
        return grant
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except (ValidationError, AuthorizationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )


@router.post("/{grant_id}/reject", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_APPROVE)
async def reject_permission_grant(
    grant_id: int,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Reject permission grant"""
    try:
        permission_service = PermissionService(db)
        grant = await permission_service.reject_permission_request(
            grant_id=grant_id,
            rejector_id=current_user["user_id"],
            reason=reason
        )
        return grant
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except (ValidationError, AuthorizationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.post("/{grant_id}/revoke", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_REVOKE)
async def revoke_permission_grant(
    grant_id: int,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Revoke permission grant"""
    try:
        permission_service = PermissionService(db)
        grant = await permission_service.revoke_permission(
            grant_id=grant_id,
            revoker_id=current_user["user_id"],
            reason=reason
        )
        return grant
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except (ValidationError, AuthorizationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.post("/{grant_id}/extend", response_model=PermissionGrantResponse)
@require_permission(Permission.PERMISSION_UPDATE)
async def extend_permission_grant(
    grant_id: int,
    new_expiry: datetime,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Extend permission grant expiry"""
    try:
        permission_service = PermissionService(db)
        grant = await permission_service.extend_permission(
            grant_id=grant_id,
            new_expiry=new_expiry,
            extender_id=current_user["user_id"]
        )
        return grant
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )