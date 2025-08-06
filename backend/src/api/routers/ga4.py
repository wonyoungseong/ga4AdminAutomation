"""
Google Analytics 4 API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Dict, Any
from datetime import datetime

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
    account_id: str = Query(None, description="Filter by GA4 account ID"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List Google Analytics 4 properties with permission-based filtering.
    
    Required permissions: GA4_PROPERTY_READ (ADMIN+ or assigned users)
    """
    try:
        ga_service = GoogleAnalyticsService()
        
        # Get user's accessible properties based on role and assignments
        user_role = current_user.get("role", "viewer")
        user_id = current_user.get("user_id")
        
        if user_role in ["super_admin", "admin"]:
            # Admins see all properties
            properties = await ga_service.list_properties(account_id=account_id)
        else:
            # Regular users see only assigned properties
            # This would integrate with client assignment system
            properties = await ga_service.list_user_properties(
                user_id=user_id, 
                account_id=account_id
            )
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        return {
            "properties": properties[start_idx:end_idx],
            "total": len(properties),
            "page": page,
            "per_page": limit,
            "pages": (len(properties) + limit - 1) // limit
        }
        
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/properties/{property_id}")
@require_permission(Permission.GA4_PROPERTY_READ)
async def get_ga4_property(
    property_id: str,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get specific GA4 property details.
    
    Required permissions: GA4_PROPERTY_READ (ADMIN+ or assigned users)
    """
    try:
        ga_service = GoogleAnalyticsService()
        
        # Check if user has access to this property
        user_role = current_user.get("role", "viewer")
        user_id = current_user.get("user_id")
        
        if user_role not in ["super_admin", "admin"]:
            # Check property assignment for regular users
            has_access = await ga_service.check_user_property_access(
                user_id=user_id,
                property_id=property_id
            )
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to GA4 property {property_id}"
                )
        
        property_details = await ga_service.get_property(property_id)
        return property_details
        
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/properties/{property_id}/permissions")
@require_permission(Permission.GA4_PROPERTY_READ)
async def get_property_permissions(
    property_id: str,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current permissions for a GA4 property.
    
    Required permissions: GA4_PROPERTY_READ (ADMIN+ or assigned users)
    """
    try:
        ga_service = GoogleAnalyticsService()
        
        # Verify property access
        user_role = current_user.get("role", "viewer")
        user_id = current_user.get("user_id")
        
        if user_role not in ["super_admin", "admin"]:
            has_access = await ga_service.check_user_property_access(
                user_id=user_id,
                property_id=property_id
            )
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to GA4 property {property_id}"
                )
        
        # Get property permissions
        permissions = await ga_service.get_property_permissions(property_id)
        
        return {
            "property_id": property_id,
            "permissions": permissions,
            "total_users": len(permissions),
            "queried_at": datetime.utcnow().isoformat(),
            "queried_by": user_id
        }
        
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/properties/{property_id}/grant-permission")
@require_permission(Permission.GA4_PROPERTY_UPDATE)
async def grant_property_permission(
    property_id: str,
    permission_data: dict,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Grant permission to a GA4 property (usually triggered by approval workflow).
    
    Required permissions: GA4_PROPERTY_UPDATE (ADMIN+ only)
    """
    try:
        ga_service = GoogleAnalyticsService()
        
        # Extract permission details
        target_email = permission_data.get("target_email")
        role = permission_data.get("role", "VIEWER")  # GA4 roles: VIEWER, ANALYST, EDITOR, ADMIN
        
        if not target_email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="target_email is required"
            )
        
        # Grant permission via Google API
        result = await ga_service.grant_property_permission(
            property_id=property_id,
            target_email=target_email,
            role=role
        )
        
        return {
            "property_id": property_id,
            "target_email": target_email,
            "role": role,
            "granted_at": datetime.utcnow().isoformat(),
            "granted_by": current_user.get("user_id"),
            "google_api_result": result
        }
        
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.delete("/properties/{property_id}/revoke-permission")
@require_permission(Permission.GA4_PROPERTY_UPDATE)
async def revoke_property_permission(
    property_id: str,
    target_email: str = Query(..., description="Email of user to revoke permission from"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Revoke permission from a GA4 property.
    
    Required permissions: GA4_PROPERTY_UPDATE (ADMIN+ only)
    """
    try:
        ga_service = GoogleAnalyticsService()
        
        # Revoke permission via Google API
        result = await ga_service.revoke_property_permission(
            property_id=property_id,
            target_email=target_email
        )
        
        return {
            "property_id": property_id,
            "target_email": target_email,
            "revoked_at": datetime.utcnow().isoformat(),
            "revoked_by": current_user.get("user_id"),
            "google_api_result": result
        }
        
    except GoogleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google API error: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


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