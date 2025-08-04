"""
Google Analytics 4 API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Dict, Any

from ...core.database import get_db
from ...core.exceptions import GoogleAPIError
from ...models.schemas import MessageResponse
from ...services.auth_service import AuthService
from ...services.google_api_service import GoogleAnalyticsService

router = APIRouter()


@router.get("/accounts")
async def list_ga4_accounts(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> List[Dict[str, Any]]:
    """List all Google Analytics accounts"""
    # Only admins and super admins can list accounts
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
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
async def list_ga4_properties(
    account_name: str,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> List[Dict[str, Any]]:
    """List properties for a specific account"""
    # Only admins and super admins can list properties
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
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
async def get_property_users(
    property_name: str,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> List[Dict[str, Any]]:
    """Get users for a specific property"""
    # Only admins and super admins can view property users
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
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
async def validate_property_access(
    property_name: str,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Validate if service account has access to manage the property"""
    # Only admins and super admins can validate property access
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
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