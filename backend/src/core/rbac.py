"""
RBAC (Role-Based Access Control) Core System
Enhanced permission management with decorators and middleware
"""

from functools import wraps
from typing import List, Optional, Dict, Any, Callable, Union
from enum import Enum
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.db_models import User, UserRole, UserStatus, RegistrationStatus
from ..core.database import get_db
from ..services.auth_service import AuthService


class Permission(str, Enum):
    """System permissions enumeration"""
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read" 
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_APPROVE = "user:approve"
    USER_ASSIGN_ROLE = "user:assign_role"
    
    # Client Management  
    CLIENT_CREATE = "client:create"
    CLIENT_READ = "client:read"
    CLIENT_UPDATE = "client:update"
    CLIENT_DELETE = "client:delete"
    CLIENT_ASSIGN_USER = "client:assign_user"
    
    # Permission Management
    PERMISSION_CREATE = "permission:create"
    PERMISSION_READ = "permission:read"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"
    PERMISSION_APPROVE = "permission:approve"
    PERMISSION_REVOKE = "permission:revoke"
    
    # Service Account Management
    SERVICE_ACCOUNT_CREATE = "service_account:create"
    SERVICE_ACCOUNT_READ = "service_account:read"
    SERVICE_ACCOUNT_UPDATE = "service_account:update"
    SERVICE_ACCOUNT_DELETE = "service_account:delete"
    
    # GA4 Property Management
    GA4_PROPERTY_CREATE = "ga4_property:create"
    GA4_PROPERTY_READ = "ga4_property:read"
    GA4_PROPERTY_UPDATE = "ga4_property:update"
    GA4_PROPERTY_DELETE = "ga4_property:delete"
    
    # Audit and Reporting
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    REPORT_GENERATE = "report:generate"
    REPORT_DOWNLOAD = "report:download"
    
    # System Administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_HEALTH = "system:health"
    SYSTEM_BACKUP = "system:backup"


class ResourceOwnership(str, Enum):
    """Resource ownership types for fine-grained access control"""
    SELF_ONLY = "self_only"          # User can only access their own resources
    CLIENT_SCOPED = "client_scoped"  # User can access resources within their assigned clients
    ALL = "all"                      # User can access all resources (admin level)


# Role-Permission Matrix
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.SUPER_ADMIN: [
        # Full system access
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, 
        Permission.USER_DELETE, Permission.USER_APPROVE, Permission.USER_ASSIGN_ROLE,
        Permission.CLIENT_CREATE, Permission.CLIENT_READ, Permission.CLIENT_UPDATE,
        Permission.CLIENT_DELETE, Permission.CLIENT_ASSIGN_USER,
        Permission.PERMISSION_CREATE, Permission.PERMISSION_READ, Permission.PERMISSION_UPDATE,
        Permission.PERMISSION_DELETE, Permission.PERMISSION_APPROVE, Permission.PERMISSION_REVOKE,
        Permission.SERVICE_ACCOUNT_CREATE, Permission.SERVICE_ACCOUNT_READ, Permission.SERVICE_ACCOUNT_UPDATE,
        Permission.SERVICE_ACCOUNT_DELETE,
        Permission.GA4_PROPERTY_CREATE, Permission.GA4_PROPERTY_READ, Permission.GA4_PROPERTY_UPDATE,
        Permission.GA4_PROPERTY_DELETE,
        Permission.AUDIT_READ, Permission.AUDIT_EXPORT, Permission.REPORT_GENERATE, Permission.REPORT_DOWNLOAD,
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_HEALTH, Permission.SYSTEM_BACKUP,
    ],
    
    UserRole.ADMIN: [
        # User management (limited)
        Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_APPROVE, Permission.USER_ASSIGN_ROLE,
        # Client management
        Permission.CLIENT_READ, Permission.CLIENT_UPDATE, Permission.CLIENT_ASSIGN_USER,
        # Permission management
        Permission.PERMISSION_READ, Permission.PERMISSION_APPROVE, Permission.PERMISSION_REVOKE,
        # Service accounts (read/update)
        Permission.SERVICE_ACCOUNT_READ, Permission.SERVICE_ACCOUNT_UPDATE,
        # GA4 properties
        Permission.GA4_PROPERTY_READ, Permission.GA4_PROPERTY_UPDATE,
        # Audit (read only)
        Permission.AUDIT_READ, Permission.REPORT_GENERATE, Permission.REPORT_DOWNLOAD,
        # System health monitoring
        Permission.SYSTEM_HEALTH,
    ],
    
    UserRole.MANAGER: [
        # Limited user management
        Permission.USER_READ, Permission.USER_UPDATE,
        # Client management (assigned clients)
        Permission.CLIENT_READ, Permission.CLIENT_UPDATE, Permission.CLIENT_ASSIGN_USER,
        # Permission management (limited)
        Permission.PERMISSION_READ, Permission.PERMISSION_APPROVE,
        # Service accounts (read)
        Permission.SERVICE_ACCOUNT_READ,
        # GA4 properties (assigned clients)
        Permission.GA4_PROPERTY_READ, Permission.GA4_PROPERTY_UPDATE,
        # Reports
        Permission.REPORT_GENERATE,
    ],
    
    UserRole.USER: [
        # Self-profile management
        Permission.USER_READ,  # Limited to self
        Permission.USER_UPDATE,  # Limited to self
        # Permission requests
        Permission.PERMISSION_READ,  # Limited to own permissions
        # Client info (limited)
        Permission.CLIENT_READ,  # Limited to assigned clients
        # GA4 properties (read for assigned clients)
        Permission.GA4_PROPERTY_READ,  # Limited to assigned clients
    ],
    
    UserRole.CLIENT: [
        # Read-only access to own data
        Permission.USER_READ,  # Limited to self
        Permission.CLIENT_READ,  # Limited to own client
        Permission.PERMISSION_READ,  # Limited to own permissions
        Permission.GA4_PROPERTY_READ,  # Limited to own client
    ],
    
    UserRole.REQUESTER: [
        # Self-profile management
        Permission.USER_READ,  # Limited to self
        Permission.USER_UPDATE,  # Limited to self
        # Permission requests
        Permission.PERMISSION_READ,  # Limited to own permissions
        # Client info (limited)
        Permission.CLIENT_READ,  # Limited to assigned clients
        # GA4 properties (read for assigned clients)
        Permission.GA4_PROPERTY_READ,  # Limited to assigned clients
    ],
    
    UserRole.VIEWER: [
        # Read-only access
        Permission.USER_READ,  # Limited to self
        Permission.CLIENT_READ,  # Limited to assigned clients
        Permission.PERMISSION_READ,  # Limited to own permissions
        Permission.GA4_PROPERTY_READ,  # Limited to assigned clients
    ],
}

# Resource ownership matrix
RESOURCE_OWNERSHIP: Dict[UserRole, ResourceOwnership] = {
    UserRole.SUPER_ADMIN: ResourceOwnership.ALL,
    UserRole.ADMIN: ResourceOwnership.ALL,
    UserRole.MANAGER: ResourceOwnership.CLIENT_SCOPED,
    UserRole.USER: ResourceOwnership.CLIENT_SCOPED,
    UserRole.CLIENT: ResourceOwnership.SELF_ONLY,
    UserRole.REQUESTER: ResourceOwnership.CLIENT_SCOPED,
    UserRole.VIEWER: ResourceOwnership.CLIENT_SCOPED,
}


class RBACService:
    """Role-Based Access Control Service"""
    
    @staticmethod
    def get_role_permissions(role: UserRole) -> List[Permission]:
        """Get all permissions for a role"""
        return ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def has_permission(role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        return permission in ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def get_resource_ownership(role: UserRole) -> ResourceOwnership:
        """Get resource ownership level for a role"""
        return RESOURCE_OWNERSHIP.get(role, ResourceOwnership.SELF_ONLY)
    
    @staticmethod
    def can_access_user(actor_role: UserRole, actor_user_id: int, 
                       target_user_id: int, client_ids: Optional[List[int]] = None) -> bool:
        """Check if actor can access target user based on role and client assignments"""
        ownership = RBACService.get_resource_ownership(actor_role)
        
        if ownership == ResourceOwnership.ALL:
            return True
        elif ownership == ResourceOwnership.SELF_ONLY:
            return actor_user_id == target_user_id
        elif ownership == ResourceOwnership.CLIENT_SCOPED:
            # For client-scoped access, would need to check shared client assignments
            # This would require database queries in actual implementation
            if actor_user_id == target_user_id:
                return True
            # Additional client-based logic would be implemented here
            return False
        
        return False
    
    @staticmethod  
    def can_manage_role(actor_role: UserRole, target_role: UserRole) -> bool:
        """Check if actor can manage (assign/revoke) target role"""
        # Use the hierarchy levels from UserRole model
        actor_level = UserRole.get_hierarchy_level(actor_role)
        target_level = UserRole.get_hierarchy_level(target_role)
        
        # Only super admin can manage super admin role
        if target_role == UserRole.SUPER_ADMIN:
            return actor_role == UserRole.SUPER_ADMIN
            
        # Higher level roles can manage lower level roles
        return actor_level > target_level


def require_permission(permission: Permission, 
                      resource_ownership: bool = False,
                      allow_self_access: bool = False):
    """
    Decorator to require specific permission for endpoint access
    
    Args:
        permission: Required permission
        resource_ownership: If True, apply resource ownership rules
        allow_self_access: If True, allow users to access their own resources
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user from dependencies
            current_user = None
            db = None
            
            # Find current_user and db in function arguments
            for arg in args:
                if isinstance(arg, dict) and 'user_id' in arg:
                    current_user = arg
                elif hasattr(arg, 'execute'):  # AsyncSession
                    db = arg
            
            # Also check kwargs
            if not current_user:
                current_user = kwargs.get('current_user')
            if not db:
                db = kwargs.get('db')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = UserRole(current_user.get('role', 'Viewer'))
            
            # Check permission
            if not RBACService.has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}",
                    headers={"X-Required-Permission": permission.value}
                )
            
            # Apply resource ownership rules if enabled
            if resource_ownership:
                # Extract target user ID from path parameters
                target_user_id = kwargs.get('user_id')
                if target_user_id and allow_self_access:
                    if not RBACService.can_access_user(
                        user_role, 
                        current_user.get('user_id'), 
                        target_user_id
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Cannot access this resource"
                        )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(allowed_roles: Union[UserRole, List[UserRole]], 
                allow_higher: bool = True):
    """
    Decorator to require specific role(s) for endpoint access
    
    Args:
        allowed_roles: Single role or list of allowed roles
        allow_higher: If True, higher-level roles are also allowed
    """
    if isinstance(allowed_roles, UserRole):
        allowed_roles = [allowed_roles]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user from arguments
            current_user = None
            for arg in args:
                if isinstance(arg, dict) and 'user_id' in arg:
                    current_user = arg
                    break
            
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = UserRole(current_user.get('role', 'Viewer'))
            
            # Check if user has required role
            if user_role not in allowed_roles:
                if allow_higher:
                    # Check if user has higher-level role
                    user_level = UserRole.get_hierarchy_level(user_role)
                    required_levels = [UserRole.get_hierarchy_level(role) for role in allowed_roles]
                    min_required_level = min(required_levels) if required_levels else 0
                    
                    if user_level < min_required_level:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Insufficient role. Required: {[r.value for r in allowed_roles]}",
                            headers={"X-Required-Roles": ",".join([r.value for r in allowed_roles])}
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required role: {[r.value for r in allowed_roles]}",
                        headers={"X-Required-Roles": ",".join([r.value for r in allowed_roles])}
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def get_current_user_with_permissions(
    current_user = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Enhanced current user dependency with permissions"""
    
    # Get full user data
    from ..services.user_service import UserService
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user can access system
    if not user.can_access_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active or not approved"
        )
    
    # Add permissions to user data
    permissions = RBACService.get_role_permissions(user.role)
    ownership = RBACService.get_resource_ownership(user.role)
    
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "status": user.status.value,
        "registration_status": user.registration_status.value,
        "permissions": [p.value for p in permissions],
        "resource_ownership": ownership.value,
        "is_approved": user.is_approved,
        "can_access_system": user.can_access_system,
    }


class RBACMiddleware:
    """RBAC Middleware for request-level authorization"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip RBAC for public endpoints
        public_paths = [
            "/health", "/api/docs", "/api/redoc", "/api/openapi.json",
            "/api/auth/login", "/api/auth/register", "/static"
        ]
        
        if any(request.url.path.startswith(path) for path in public_paths):
            await self.app(scope, receive, send)
            return
        
        # Add RBAC context to request state
        request.state.rbac_enabled = True
        
        await self.app(scope, receive, send)


def check_resource_access(user: Dict[str, Any], resource_type: str, 
                         resource_id: Optional[str] = None, 
                         client_ids: Optional[List[int]] = None) -> bool:
    """
    Check if user can access a specific resource
    
    Args:
        user: Current user data with permissions
        resource_type: Type of resource (user, client, permission, etc.)
        resource_id: ID of specific resource 
        client_ids: List of client IDs user has access to
    """
    ownership = ResourceOwnership(user.get("resource_ownership", "self_only"))
    
    if ownership == ResourceOwnership.ALL:
        return True
    
    if ownership == ResourceOwnership.SELF_ONLY:
        # For self-only access, user can only access their own resources
        if resource_type == "user":
            return resource_id is None or str(user["user_id"]) == resource_id
        return False
    
    if ownership == ResourceOwnership.CLIENT_SCOPED:
        # For client-scoped access, check if resource belongs to user's clients
        if resource_type == "user":
            return resource_id is None or str(user["user_id"]) == resource_id
        # Additional client-scoped logic would be implemented here
        return True
    
    return False


# Permission validation utilities
def validate_role_transition(current_role: UserRole, new_role: UserRole, 
                           actor_role: UserRole) -> bool:
    """Validate if role transition is allowed"""
    
    # Self-role changes not allowed
    if current_role == new_role:
        return True
    
    # Check if actor can manage the target role
    if not RBACService.can_manage_role(actor_role, new_role):
        return False
    
    # Additional business rules
    # Super Admin -> Admin requires Super Admin actor
    if current_role == UserRole.SUPER_ADMIN and new_role == UserRole.ADMIN:
        return actor_role == UserRole.SUPER_ADMIN
    
    # Admin -> Super Admin requires Super Admin actor  
    if current_role == UserRole.ADMIN and new_role == UserRole.SUPER_ADMIN:
        return actor_role == UserRole.SUPER_ADMIN
    
    return True


def get_allowed_actions(user_role: UserRole, resource_type: str) -> List[str]:
    """Get list of allowed actions for a role on a resource type"""
    permissions = RBACService.get_role_permissions(user_role)
    actions = []
    
    # Map permissions to actions based on resource type
    permission_mapping = {
        "user": {
            Permission.USER_CREATE: "create",
            Permission.USER_READ: "read", 
            Permission.USER_UPDATE: "update",
            Permission.USER_DELETE: "delete",
            Permission.USER_ASSIGN_ROLE: "assign_role",
            Permission.USER_APPROVE: "approve",
        },
        "client": {
            Permission.CLIENT_CREATE: "create",
            Permission.CLIENT_READ: "read",
            Permission.CLIENT_UPDATE: "update", 
            Permission.CLIENT_DELETE: "delete",
            Permission.CLIENT_ASSIGN_USER: "assign_user",
        },
        "permission": {
            Permission.PERMISSION_CREATE: "create",
            Permission.PERMISSION_READ: "read",
            Permission.PERMISSION_UPDATE: "update",
            Permission.PERMISSION_DELETE: "delete",
            Permission.PERMISSION_APPROVE: "approve",
            Permission.PERMISSION_REVOKE: "revoke",
        },
    }
    
    resource_permissions = permission_mapping.get(resource_type, {})
    for permission, action in resource_permissions.items():
        if permission in permissions:
            actions.append(action)
    
    return actions