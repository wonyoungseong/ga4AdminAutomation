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
from ...services.auth_service import AuthService
from ...services.permission_service import PermissionService

router = APIRouter()


@router.post("/", response_model=PermissionGrantResponse)
async def create_permission_request(
    grant_data: PermissionGrantCreate,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
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
async def list_permission_grants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status_filter: Optional[PermissionStatus] = Query(None, alias="status"),
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """List permission grants"""
    permission_service = PermissionService(db)
    
    # Regular users can only see their own grants
    if current_user.get("role") not in ["admin", "super_admin", "Admin", "Super Admin"]:
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
async def get_permission_grant(
    grant_id: int,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get permission grant by ID"""
    permission_service = PermissionService(db)
    grant = await permission_service.get_permission_grant(grant_id)
    
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission grant not found"
        )
    
    # Check if user can access this grant
    if (current_user.get("role") not in ["admin", "super_admin", "Admin", "Super Admin"] and 
        grant.user_id != current_user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return grant


@router.put("/{grant_id}", response_model=PermissionGrantResponse)
async def update_permission_grant(
    grant_id: int,
    grant_data: PermissionGrantUpdate,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Update permission grant"""
    # Only admins can update grants
    if current_user.get("role") not in ["admin", "super_admin", "Admin", "Super Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # TODO: Implement update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update functionality not yet implemented"
    )


@router.post("/{grant_id}/approve", response_model=PermissionGrantResponse)
async def approve_permission_grant(
    grant_id: int,
    notes: Optional[str] = None,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
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
async def reject_permission_grant(
    grant_id: int,
    reason: Optional[str] = None,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
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
async def revoke_permission_grant(
    grant_id: int,
    reason: Optional[str] = None,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
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
async def extend_permission_grant(
    grant_id: int,
    new_expiry: datetime,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
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