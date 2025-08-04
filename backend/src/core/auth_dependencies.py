"""
Authentication and authorization dependencies with client access control
"""

from typing import List, Optional, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from datetime import datetime

from .database import get_db
from .config import settings
from .exceptions import AuthenticationError, PermissionDeniedError
from ..models.db_models import User, UserRole
from ..services.client_assignment_service import ClientAssignmentService


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Invalid token")
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            raise AuthenticationError("Token expired")
            
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    
    # Get user from database
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise AuthenticationError("User not found")
    
    if user.status.value != "active":
        raise AuthenticationError("User account is not active")
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for backward compatibility)"""
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """Decorator to require specific user roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (should be injected by FastAPI)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise AuthenticationError("Authentication required")
            
            if current_user.role not in allowed_roles:
                raise PermissionDeniedError(
                    f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions based on role hierarchy"""
    
    # Define role-based permissions
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
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise AuthenticationError("Authentication required")
            
            # Check permissions
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            missing_permissions = [p for p in permissions if p not in user_permissions]
            
            if missing_permissions:
                raise PermissionDeniedError(
                    f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def require_client_access(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to ensure user has access to specific client"""
    
    client_service = ClientAssignmentService(db)
    has_access = await client_service.check_user_client_access(
        user_id=current_user.id,
        client_id=client_id,
        user_role=current_user.role
    )
    
    if not has_access:
        raise PermissionDeniedError(f"Access denied to client {client_id}")
    
    return current_user


def require_client_access_param(client_id_param: str = "client_id"):
    """Dependency factory to require client access from path/query parameter"""
    
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        **kwargs
    ) -> User:
        # Extract client_id from path parameters
        client_id = kwargs.get(client_id_param)
        if client_id is None:
            raise ValueError(f"Client ID parameter '{client_id_param}' not found")
        
        client_service = ClientAssignmentService(db)
        has_access = await client_service.check_user_client_access(
            user_id=current_user.id,
            client_id=int(client_id),
            user_role=current_user.role
        )
        
        if not has_access:
            raise PermissionDeniedError(f"Access denied to client {client_id}")
        
        return current_user
    
    return dependency


async def get_user_accessible_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[int]:
    """Get list of client IDs accessible to current user"""
    
    client_service = ClientAssignmentService(db)
    return await client_service.get_user_accessible_clients(
        user_id=current_user.id,
        user_role=current_user.role
    )


def client_access_filter():
    """Decorator to automatically filter results by client access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user and accessible clients
            current_user = None
            accessible_clients = None
            
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif isinstance(value, list) and key == "accessible_clients":
                    accessible_clients = value
            
            if not current_user:
                raise AuthenticationError("Authentication required")
            
            # Super Admins have access to all clients
            if current_user.role == UserRole.SUPER_ADMIN:
                kwargs["client_filter"] = None  # No filter needed
            else:
                # Add client filter to kwargs
                if accessible_clients is None:
                    # This should be injected by dependency
                    raise ValueError("Accessible clients not provided")
                kwargs["client_filter"] = accessible_clients
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# RBAC Helper Functions

def can_manage_user_role(manager_role: UserRole, target_role: UserRole) -> bool:
    """Check if manager can manage target user role"""
    if manager_role == UserRole.SUPER_ADMIN:
        return True
    elif manager_role == UserRole.ADMIN:
        return target_role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    return False


def can_access_user(current_user_role: UserRole, current_user_id: int, target_user_id: int) -> bool:
    """Check if user can access another user's information"""
    if current_user_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return True
    return current_user_id == target_user_id


def get_role_hierarchy_access(user_role: UserRole) -> List[UserRole]:
    """Get roles that the user can access based on hierarchy"""
    hierarchy = {
        UserRole.SUPER_ADMIN: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.REQUESTER, UserRole.VIEWER],
        UserRole.ADMIN: [UserRole.ADMIN, UserRole.REQUESTER, UserRole.VIEWER],
        UserRole.REQUESTER: [UserRole.REQUESTER, UserRole.VIEWER],
        UserRole.VIEWER: [UserRole.VIEWER]
    }
    return hierarchy.get(user_role, [UserRole.VIEWER])


# Permission validation for different operations

async def validate_client_operation_access(
    operation: str,
    client_id: Optional[int],
    current_user: User,
    db: AsyncSession
) -> bool:
    """Validate access for client-related operations"""
    
    # Super Admins can perform all operations
    if current_user.role == UserRole.SUPER_ADMIN:
        return True
    
    # Admins can perform most operations
    if current_user.role == UserRole.ADMIN:
        if operation in ["create", "read", "update", "delete", "assign_users"]:
            return True
    
    # For specific client operations, check assignment
    if client_id and operation in ["read", "create_permission"]:
        client_service = ClientAssignmentService(db)
        return await client_service.check_user_client_access(
            user_id=current_user.id,
            client_id=client_id,
            user_role=current_user.role
        )
    
    return False


async def validate_user_operation_access(
    operation: str,
    target_user_id: Optional[int],
    current_user: User,
    db: AsyncSession
) -> bool:
    """Validate access for user-related operations"""
    
    # Super Admins can perform all operations
    if current_user.role == UserRole.SUPER_ADMIN:
        return True
    
    # Admins can manage non-admin users
    if current_user.role == UserRole.ADMIN:
        if operation in ["create", "read", "update", "delete"]:
            if target_user_id:
                # Check if target user is manageable
                query = select(User).where(User.id == target_user_id)
                result = await db.execute(query)
                target_user = result.scalar_one_or_none()
                if target_user:
                    return can_manage_user_role(current_user.role, target_user.role)
            return True
    
    # Users can only access their own information
    if target_user_id and operation in ["read", "update"]:
        return current_user.id == target_user_id
    
    return False