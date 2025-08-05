"""
Role Management API routes - RBAC Role Assignment System
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from ...core.database import get_db
from ...core.auth_dependencies import (
    get_current_user, 
    require_permissions,
    can_manage_user_role,
    validate_user_operation_access
)
from ...core.exceptions import PermissionDeniedError, NotFoundError
from ...models.db_models import User, UserRole
from ...models.schemas import UserResponse
from ...services.user_service import UserService

router = APIRouter()


@router.put("/{user_id}/role")
@require_permissions(["change_user_role"])
async def assign_user_role(
    user_id: int,
    role_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign role to user.
    
    Required permissions: change_user_role (SUPER_ADMIN+ only)
    """
    try:
        new_role = UserRole(role_data.get("role"))
        
        # Check if current user can assign this role
        if not can_manage_user_role(current_user.role, new_role):
            raise PermissionDeniedError(
                f"Cannot assign role {new_role.value}. "
                f"Your role ({current_user.role.value}) has insufficient privileges."
            )
        
        # Prevent self-demotion to lower privilege
        if current_user.id == user_id and new_role != current_user.role:
            try:
                current_level = UserRole.get_hierarchy_level(current_user.role)
                new_level = UserRole.get_hierarchy_level(new_role)
                if new_level < current_level:
                    raise PermissionDeniedError("Cannot demote your own role")
            except AttributeError:
                # Fallback if get_hierarchy_level doesn't exist
                hierarchy = {
                    UserRole.SUPER_ADMIN: 4,
                    UserRole.ADMIN: 3,
                    UserRole.REQUESTER: 2,
                    UserRole.VIEWER: 1
                }
                if hierarchy.get(new_role, 0) < hierarchy.get(current_user.role, 0):
                    raise PermissionDeniedError("Cannot demote your own role")
        
        user_service = UserService(db)
        user = await user_service.update_user_role(user_id, new_role)
        return {
            "message": f"Role updated successfully",
            "user_id": user_id,
            "previous_role": current_user.role.value if current_user.id == user_id else "unknown",
            "new_role": new_role.value,
            "updated_by": current_user.id
        }
    except (PermissionDeniedError, NotFoundError, ValueError) as e:
        status_code = status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
                     status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else \
                     status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/{user_id}/permissions")
@require_permissions(["read_user"])
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's effective permissions based on role.
    
    Required permissions: read_user (ADMIN+ for others, own permissions allowed)
    """
    try:
        # Validate access to specific user
        if not await validate_user_operation_access("read", user_id, current_user, db):
            raise PermissionDeniedError("Insufficient permissions to view this user's permissions")
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        # Define role permissions (from auth_dependencies.py)
        ROLE_PERMISSIONS = {
            UserRole.SUPER_ADMIN: [
                "create_user", "read_user", "update_user", "delete_user", "change_user_role",
                "create_client", "read_client", "update_client", "delete_client",
                "manage_client_assignments", "read_all_client_assignments",
                "read_permission", "approve_permission", "reject_permission", 
                "create_permission", "delete_permission",
                "read_audit_log", "read_all_audit_logs",
                "ga4_admin", "system_admin"
            ],
            UserRole.ADMIN: [
                "create_user", "read_user", "update_user", "delete_user",
                "create_client", "read_client", "update_client", "delete_client",
                "manage_client_assignments", "read_assigned_client_assignments",
                "read_permission", "approve_permission", "reject_permission",
                "create_permission", "delete_permission",
                "read_audit_log", "read_filtered_audit_logs",
                "ga4_admin"
            ],
            UserRole.REQUESTER: [
                "read_user", "update_own_profile",
                "read_assigned_clients", "read_own_client_assignments",
                "create_permission", "read_own_permissions",
                "read_own_audit_logs"
            ],
            UserRole.VIEWER: [
                "read_user", "update_own_profile",
                "read_assigned_clients", "read_own_client_assignments",
                "read_permissions",
                "read_own_audit_logs"
            ]
        }
        
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        return {
            "user_id": user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "permissions": user_permissions,
            "permission_count": len(user_permissions),
            "can_manage_users": "create_user" in user_permissions,
            "can_manage_clients": "create_client" in user_permissions,
            "can_approve_permissions": "approve_permission" in user_permissions,
            "system_admin": "system_admin" in user_permissions
        }
    except (PermissionDeniedError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/roles/hierarchy")
@require_permissions(["read_user"])
async def get_role_hierarchy(
    current_user: User = Depends(get_current_user)
):
    """
    Get role hierarchy and permissions matrix.
    
    Required permissions: read_user (All authenticated users)
    """
    hierarchy = {
        "roles": [
            {
                "name": "SUPER_ADMIN",
                "level": 4,
                "description": "Full system access with all permissions",
                "can_manage": ["SUPER_ADMIN", "ADMIN", "REQUESTER", "VIEWER"]
            },
            {
                "name": "ADMIN", 
                "level": 3,
                "description": "Administrative access for user and client management",
                "can_manage": ["REQUESTER", "VIEWER"]
            },
            {
                "name": "REQUESTER",
                "level": 2, 
                "description": "Can request permissions and manage own profile",
                "can_manage": []
            },
            {
                "name": "VIEWER",
                "level": 1,
                "description": "Read-only access to assigned data",
                "can_manage": []
            }
        ],
        "permissions_matrix": {
            "SUPER_ADMIN": 16,  # All permissions
            "ADMIN": 12,        # Most permissions except system admin
            "REQUESTER": 6,     # Limited permissions
            "VIEWER": 4         # Read-only permissions
        },
        "your_role": {
            "name": current_user.role.value,
            "level": {
                UserRole.SUPER_ADMIN: 4,
                UserRole.ADMIN: 3,
                UserRole.REQUESTER: 2,
                UserRole.VIEWER: 1
            }.get(current_user.role, 1)
        }
    }
    
    return hierarchy


@router.get("/manageable-roles")
@require_permissions(["change_user_role"])
async def get_manageable_roles(
    current_user: User = Depends(get_current_user)
):
    """
    Get roles that current user can assign to others.
    
    Required permissions: change_user_role (ADMIN+)
    """
    manageable_roles = []
    
    for role in UserRole:
        if can_manage_user_role(current_user.role, role):
            manageable_roles.append({
                "name": role.value,
                "description": {
                    UserRole.SUPER_ADMIN: "Full system administration",
                    UserRole.ADMIN: "User and client management", 
                    UserRole.REQUESTER: "Permission requests and profile management",
                    UserRole.VIEWER: "Read-only access"
                }.get(role, "Standard user role")
            })
    
    return {
        "your_role": current_user.role.value,
        "manageable_roles": manageable_roles,
        "count": len(manageable_roles)
    }