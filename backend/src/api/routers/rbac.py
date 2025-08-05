"""
RBAC (Role-Based Access Control) API Endpoints
Enhanced role and permission management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ...core.database import get_db
from ...core.rbac import (
    Permission, require_permission, require_role, get_current_user_with_permissions,
    RBACService, ResourceOwnership
)
from ...models.db_models import UserRole, UserStatus
from ...services.auth_service import AuthService

router = APIRouter(prefix="/api/rbac", tags=["RBAC - Role & Permission Management"])
logger = logging.getLogger(__name__)


@router.get("/check-permission")
async def check_user_permission(
    permission: str = Query(..., description="Permission to check"),
    resource_id: Optional[str] = Query(None, description="Specific resource ID"),
    client_id: Optional[int] = Query(None, description="Client context"),
    current_user: dict = Depends(get_current_user_with_permissions)
):
    """Check if current user has a specific permission"""
    try:
        # Parse permission
        perm = Permission(permission)
        user_role = UserRole(current_user["role"])
        
        # Check permission
        has_permission = RBACService.has_permission(user_role, perm)
        
        return {
            "has_permission": has_permission,
            "permission": permission,
            "user_id": current_user["user_id"],
            "resource_id": resource_id,
            "client_id": client_id,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {permission}"
        )
    except Exception as e:
        logger.error(f"Error checking permission {permission} for user {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission check failed"
        )


@router.get("/users/{user_id}/permissions")
@require_permission(Permission.USER_READ)
async def get_user_permissions(
    user_id: int = Path(..., description="User ID"),
    client_id: Optional[int] = Query(None, description="Filter by client context"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions for a specific user"""
    try:
        from ...services.user_service import UserService
        user_service = UserService(db)
        
        # Get user
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get permissions for user role
        permissions = RBACService.get_role_permissions(user.role)
        ownership = RBACService.get_resource_ownership(user.role)
        
        return {
            "user_id": user_id,
            "role": user.role.value,
            "client_id": client_id,
            "permissions": [p.value for p in permissions],
            "resource_ownership": ownership.value,
            "total_permissions": len(permissions),
            "queried_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permissions for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )


@router.get("/roles")
@require_permission(Permission.USER_READ)
async def list_available_roles(
    current_user: dict = Depends(get_current_user_with_permissions)
):
    """List all available roles with hierarchy information"""
    try:
        roles = []
        for role in UserRole:
            permissions = RBACService.get_role_permissions(role)
            ownership = RBACService.get_resource_ownership(role)
            
            # Get roles this role can manage
            manageable_roles = []
            for target_role in UserRole:
                if RBACService.can_manage_role(role, target_role):
                    manageable_roles.append(target_role.value)
            
            roles.append({
                "role": role.value,
                "level": UserRole.get_hierarchy_level(role),
                "description": _get_role_description(role),
                "permissions": [p.value for p in permissions],
                "resource_ownership": ownership.value,
                "can_manage": manageable_roles,
                "permission_count": len(permissions)
            })
        
        roles.sort(key=lambda x: x["level"], reverse=True)
        
        return {
            "roles": roles,
            "total_roles": len(roles)
        }
        
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list roles"
        )


@router.get("/permissions")
@require_permission(Permission.USER_READ)
async def list_permissions(
    resource: Optional[str] = Query(None, description="Filter by resource type"),
    current_user: dict = Depends(get_current_user_with_permissions)
):
    """Get list of all available permissions"""
    try:
        permissions = []
        
        for perm in Permission:
            # Skip if filtering by resource and doesn't match
            if resource and not perm.value.startswith(f"{resource}."):
                continue
                
            permissions.append({
                "permission": perm.value,
                "description": f"Permission to {perm.value.replace('_', ' ').lower()}"
            })
        
        return {
            "permissions": permissions,
            "total": len(permissions),
            "filtered_by_resource": resource
        }
        
    except Exception as e:
        logger.error(f"Error listing permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list permissions"
        )


@router.get("/role-hierarchy")
@require_permission(Permission.USER_READ)
async def get_role_hierarchy(
    current_user: dict = Depends(get_current_user_with_permissions)
):
    """Get role hierarchy information"""
    try:
        hierarchy = {}
        
        for role in UserRole:
            hierarchy[role.value] = {
                "level": UserRole.get_hierarchy_level(role),
                "can_manage": [r.value for r in UserRole if role.can_manage(r)],
                "inherits_from": [r.value for r in UserRole if role.inherits_from(r) and r != role]
            }
        
        return {
            "hierarchy": hierarchy,
            "explanation": {
                "level": "Higher numbers can manage lower numbers",
                "can_manage": "Roles this role can assign/modify",
                "inherits_from": "Roles this role inherits permissions from"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting role hierarchy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get role hierarchy"
        )


def _get_role_description(role: UserRole) -> str:
    """Get human-readable role description"""
    descriptions = {
        UserRole.SUPER_ADMIN: "Complete system control and administration",
        UserRole.ADMIN: "Full system operations and user management",
        UserRole.MANAGER: "Client-specific management and team oversight",
        UserRole.USER: "Standard operations within assigned clients",
        UserRole.CLIENT: "Limited read-only access to own data",
        UserRole.VIEWER: "Read-only access (legacy role)",
        UserRole.REQUESTER: "Can request permissions (legacy role)"
    }
    return descriptions.get(role, "No description available")