"""
Service Accounts API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional, List
from datetime import datetime

from ...core.database import get_db
from ...core.exceptions import NotFoundError, ValidationError, AuthorizationError, GoogleAPIError
from ...models.schemas import (
    ServiceAccountResponse, ServiceAccountCreate, ServiceAccountUpdate, 
    MessageResponse, PaginatedResponse, GA4PropertyResponse
)
from ...core.rbac import Permission, require_permission, get_current_user_with_permissions
from ...services.service_account_service import ServiceAccountService

router = APIRouter()


@router.post("/", response_model=ServiceAccountResponse)
@require_permission(Permission.SERVICE_ACCOUNT_CREATE)
async def create_service_account(
    sa_data: ServiceAccountCreate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Create a new service account"""
    try:
        sa_service = ServiceAccountService(db)
        service_account = await sa_service.create_service_account(
            sa_data=sa_data,
            created_by_id=current_user["user_id"]
        )
        return service_account
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google API Error: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse[ServiceAccountResponse])
@require_permission(Permission.SERVICE_ACCOUNT_READ)
async def list_service_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    client_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """List service accounts with pagination and filters"""
    sa_service = ServiceAccountService(db)
    
    # Apply client access control for non-admin users
    accessible_client_ids = None
    if current_user.get("role") not in ["super_admin", "admin"]:
        from ...services.client_assignment_service import ClientAssignmentService
        ca_service = ClientAssignmentService(db)
        accessible_client_ids = await ca_service.get_user_accessible_client_ids(
            current_user["user_id"]
        )
    
    result = await sa_service.list_service_accounts(
        skip=skip,
        limit=limit,
        client_id=client_id,
        is_active=is_active,
        accessible_client_ids=accessible_client_ids
    )
    
    return result


@router.get("/{sa_id}", response_model=ServiceAccountResponse)
@require_permission(Permission.SERVICE_ACCOUNT_READ)
async def get_service_account(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get service account by ID"""
    sa_service = ServiceAccountService(db)
    service_account = await sa_service.get_service_account(sa_id)
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
    
    # Check access permissions for non-admin users
    if current_user.get("role") not in ["super_admin", "admin"]:
        from ...services.client_assignment_service import ClientAssignmentService
        ca_service = ClientAssignmentService(db)
        accessible_client_ids = await ca_service.get_user_accessible_client_ids(
            current_user["user_id"]
        )
        
        if service_account.client_id not in accessible_client_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this service account"
            )
    
    return service_account


@router.put("/{sa_id}", response_model=ServiceAccountResponse)
@require_permission(Permission.SERVICE_ACCOUNT_UPDATE)
async def update_service_account(
    sa_id: int,
    sa_data: ServiceAccountUpdate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Update service account"""
    try:
        sa_service = ServiceAccountService(db)
        service_account = await sa_service.update_service_account(
            sa_id=sa_id,
            sa_data=sa_data,
            updated_by_id=current_user["user_id"]
        )
        return service_account
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/{sa_id}", response_model=MessageResponse)
@require_permission(Permission.SERVICE_ACCOUNT_UPDATE)
async def delete_service_account(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Delete service account"""
    try:
        sa_service = ServiceAccountService(db)
        await sa_service.delete_service_account(
            sa_id=sa_id,
            deleted_by_id=current_user["user_id"]
        )
        return MessageResponse(message="Service account deleted successfully")
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{sa_id}/validate", response_model=dict)
@require_permission(Permission.SERVICE_ACCOUNT_UPDATE)
async def validate_service_account(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Validate service account credentials and permissions"""
    try:
        sa_service = ServiceAccountService(db)
        validation_result = await sa_service.validate_service_account(sa_id)
        return validation_result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google API Error: {str(e)}"
        )


@router.post("/{sa_id}/discover-properties", response_model=List[GA4PropertyResponse])
@require_permission(Permission.SERVICE_ACCOUNT_UPDATE)
async def discover_ga4_properties(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Discover GA4 properties accessible by this service account"""
    try:
        sa_service = ServiceAccountService(db)
        properties = await sa_service.discover_properties(
            sa_id=sa_id,
            discovered_by_id=current_user["user_id"]
        )
        return properties
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google API Error: {str(e)}"
        )


@router.get("/{sa_id}/properties", response_model=List[GA4PropertyResponse])
@require_permission(Permission.SERVICE_ACCOUNT_READ)
async def list_service_account_properties(
    sa_id: int,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """List GA4 properties associated with this service account"""
    try:
        sa_service = ServiceAccountService(db)
        properties = await sa_service.list_service_account_properties(
            sa_id=sa_id,
            is_active=is_active
        )
        return properties
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{sa_id}/health", response_model=dict)
@require_permission(Permission.SERVICE_ACCOUNT_READ)
async def get_service_account_health(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get service account health status"""
    try:
        sa_service = ServiceAccountService(db)
        health_status = await sa_service.get_health_status(sa_id)
        return health_status
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{sa_id}/health/check", response_model=dict)
@require_permission(Permission.SERVICE_ACCOUNT_UPDATE)
async def check_service_account_health(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Perform health check on service account"""
    try:
        sa_service = ServiceAccountService(db)
        health_result = await sa_service.perform_health_check(
            sa_id=sa_id,
            checked_by_id=current_user["user_id"]
        )
        return health_result
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google API Error: {str(e)}"
        )


@router.post("/{sa_id}/rotate-credentials", response_model=ServiceAccountResponse)
@require_permissions(["manage_service_accounts", "system_admin"])
async def rotate_service_account_credentials(
    sa_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Rotate service account credentials (Super Admin only)"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can rotate service account credentials"
        )
    
    try:
        sa_service = ServiceAccountService(db)
        service_account = await sa_service.rotate_credentials(
            sa_id=sa_id,
            rotated_by_id=current_user["user_id"]
        )
        return service_account
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google API Error: {str(e)}"
        )