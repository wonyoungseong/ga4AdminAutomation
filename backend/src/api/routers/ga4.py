"""
Google Analytics 4 API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Dict, Any

from ...core.database import get_db
from ...core.exceptions import GoogleAPIError
from ...models.schemas import MessageResponse
from ...core.rbac import Permission, require_permission, get_current_user_with_permissions
from ...services.google_api_service import GoogleAnalyticsService

router = APIRouter()


@router.get("/")
@require_permission(Permission.GA4_PROPERTY_READ)
async def list_ga4_properties(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all Google Analytics properties"""
    # Return empty list for now (placeholder)
    return []


@router.get("/accounts")
@require_permission(Permission.GA4_PROPERTY_READ)
async def list_ga4_accounts(
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all Google Analytics accounts"""
    # RBAC decorator handles access control
    
    try:
        ga_service = GoogleAnalyticsService()
        accounts = await ga_service.list_accounts()
        return accounts
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )


@router.get("/accounts/{account_name}/properties")
@require_permission(Permission.GA4_PROPERTY_READ)
async def list_ga4_properties(
    account_name: str,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List properties for a specific account"""
    # RBAC decorator handles access control
    
    try:
        ga_service = GoogleAnalyticsService()
        properties = await ga_service.list_properties(account_name)
        return properties
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )


@router.get("/properties/{property_name}/users")
@require_permission(Permission.GA4_PROPERTY_READ)
async def get_property_users(
    property_name: str,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get users for a specific property"""
    # RBAC decorator handles access control
    
    try:
        ga_service = GoogleAnalyticsService()
        users = await ga_service.get_property_users(property_name)
        return users
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )


@router.post("/properties/{property_name}/validate", response_model=MessageResponse)
@require_permission(Permission.GA4_PROPERTY_READ)
async def validate_property_access(
    property_name: str,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Validate if service account has access to manage the property"""
    # RBAC decorator handles access control
    
    try:
        ga_service = GoogleAnalyticsService()
        has_access = await ga_service.validate_property_access(property_name)
        
        if has_access:
            return MessageResponse(message="Service account has access to manage this property")
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service account does not have access to manage this property"
            )
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )