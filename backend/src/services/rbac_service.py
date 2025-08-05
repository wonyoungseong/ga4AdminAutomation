"""
RBAC (Role-Based Access Control) Service

High-performance permission checking with caching and context awareness.
Supports role hierarchy, permission inheritance, and client-specific access control.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, Any, Tuple
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import logging
import json

from ..models.db_models import (
    User, UserRole, UserRoleAssignment, UserPermissionOverride,
    RolePermission, Client, ClientAssignment,
    Permission, PermissionScope, PermissionContext
)
from ..core.exceptions import AuthorizationError

logger = logging.getLogger(__name__)


class RBACService:
    """Role-Based Access Control Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._permission_cache: Dict[str, Dict] = {}
        self._cache_ttl = timedelta(minutes=5)  # 5-minute cache TTL
    
    # ==================== CORE PERMISSION CHECKING ====================
    
    async def check_permission(
        self,
        user_id: int,
        permission: Union[Permission, str],
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """
        Core permission checking method with caching
        
        Args:
            user_id: User ID to check permissions for
            permission: Permission to check (enum or string)
            resource_id: Specific resource ID (optional)
            client_id: Client context (optional)
            context: Permission context (optional)
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            # Convert string to Permission enum if needed
            if isinstance(permission, str):
                try:
                    permission = Permission(permission)
                except ValueError:
                    logger.warning(f"Invalid permission string: {permission}")
                    return False
            
            # Generate cache key
            cache_key = self._generate_cache_key(user_id, permission, resource_id, client_id, context)
            
            # Check cache first
            cached_result = self._get_cached_permission(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Perform actual permission check
            has_permission = await self._check_permission_internal(
                user_id, permission, resource_id, client_id, context
            )
            
            # Cache the result
            self._cache_permission(cache_key, has_permission)
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id}: {e}")
            # Fail secure - deny permission on error
            return False
    
    async def _check_permission_internal(
        self,
        user_id: int,
        permission: Permission,
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Internal permission checking logic"""
        
        # Get user with relationships
        user = await self._get_user_with_permissions(user_id)
        if not user:
            return False
        
        # Check if permission is explicitly denied
        if await self._is_permission_denied(user, permission, resource_id, client_id, context):
            return False
        
        # Check if permission is explicitly granted via override
        if await self._is_permission_granted_override(user, permission, resource_id, client_id, context):
            return True
        
        # Check role-based permissions
        return await self._check_role_permissions(user, permission, resource_id, client_id, context)
    
    async def _get_user_with_permissions(self, user_id: int) -> Optional[User]:
        """Get user with all permission-related relationships loaded"""
        try:
            result = await self.db.execute(
                select(User)
                .options(
                    selectinload(User.role_assignments),
                    selectinload(User.permission_overrides),
                    selectinload(User.client_assignments)
                )
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None
    
    async def _is_permission_denied(
        self,
        user: User,
        permission: Permission,
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check if permission is explicitly denied"""
        
        for override in user.permission_overrides:
            if (override.is_valid and 
                not override.is_granted and 
                override.permission == permission and
                self._context_matches(override, resource_id, client_id, context)):
                return True
        
        return False
    
    async def _is_permission_granted_override(
        self,
        user: User,
        permission: Permission,
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check if permission is explicitly granted via override"""
        
        for override in user.permission_overrides:
            if (override.is_valid and 
                override.is_granted and 
                override.permission == permission and
                self._context_matches(override, resource_id, client_id, context)):
                return True
        
        return False
    
    async def _check_role_permissions(
        self,
        user: User,
        permission: Permission,
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check role-based permissions with hierarchy and inheritance"""
        
        # Get all valid role assignments for the user
        valid_roles = self._get_valid_user_roles(user, client_id)
        
        if not valid_roles:
            return False
        
        # Check each role for the permission
        for role, role_context in valid_roles:
            if await self._role_has_permission(role, permission, role_context, resource_id, client_id, context):
                return True
        
        # Check role inheritance - higher roles inherit lower role permissions
        for role, role_context in valid_roles:
            if await self._check_inherited_permissions(role, permission, role_context, resource_id, client_id, context):
                return True
        
        return False
    
    def _get_valid_user_roles(self, user: User, client_id: Optional[int] = None) -> List[Tuple[UserRole, Optional[int]]]:
        """Get all valid roles for a user, considering context"""
        valid_roles = []
        
        # Add primary role (from user.role)
        valid_roles.append((user.role, None))
        
        # Add role assignments
        for assignment in user.role_assignments:
            if assignment.is_valid:
                # Include system-wide roles or client-specific roles
                if assignment.client_id is None or assignment.client_id == client_id:
                    valid_roles.append((assignment.role, assignment.client_id))
        
        # Sort by role hierarchy (highest first)
        valid_roles.sort(key=lambda x: UserRole.get_hierarchy_level(x[0]), reverse=True)
        
        return valid_roles
    
    async def _role_has_permission(
        self,
        role: UserRole,
        permission: Permission,
        role_client_id: Optional[int],
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check if a specific role has a permission"""
        
        try:
            # Query role permissions
            result = await self.db.execute(
                select(RolePermission)
                .where(
                    and_(
                        RolePermission.role == role,
                        RolePermission.permission == permission,
                        RolePermission.is_active == True
                    )
                )
            )
            
            role_permissions = result.scalars().all()
            
            for role_perm in role_permissions:
                if self._role_permission_matches_context(role_perm, role_client_id, resource_id, client_id, context):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking role permission {role}:{permission}: {e}")
            return False
    
    async def _check_inherited_permissions(
        self,
        role: UserRole,
        permission: Permission,
        role_client_id: Optional[int],
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check inherited permissions from lower-level roles"""
        
        # Get all roles that this role inherits from
        inherited_roles = self._get_inherited_roles(role)
        
        for inherited_role in inherited_roles:
            if await self._role_has_permission(inherited_role, permission, role_client_id, resource_id, client_id, context):
                return True
        
        return False
    
    def _get_inherited_roles(self, role: UserRole) -> List[UserRole]:
        """Get roles that the given role inherits permissions from"""
        current_level = UserRole.get_hierarchy_level(role)
        inherited_roles = []
        
        for other_role in UserRole:
            if UserRole.get_hierarchy_level(other_role) < current_level:
                inherited_roles.append(other_role)
        
        return inherited_roles
    
    def _context_matches(
        self,
        override: UserPermissionOverride,
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check if permission override context matches the request context"""
        
        # Check client context
        if override.client_id is not None and override.client_id != client_id:
            return False
        
        # Check resource context
        if override.resource_id is not None and override.resource_id != resource_id:
            return False
        
        # Check permission context
        if context is not None and override.context != context and override.context != PermissionContext.ALL:
            return False
        
        return True
    
    def _role_permission_matches_context(
        self,
        role_perm: RolePermission,
        role_client_id: Optional[int],
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check if role permission context matches the request context"""
        
        # Check scope
        if role_perm.scope == PermissionScope.CLIENT and role_client_id != client_id:
            return False
        
        # Check context
        if context is not None and role_perm.context != context and role_perm.context != PermissionContext.ALL:
            return False
        
        return True
    
    # ==================== PERMISSION MANAGEMENT ====================
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role: UserRole,
        assigned_by_id: int,
        client_id: Optional[int] = None,
        scope: PermissionScope = PermissionScope.SYSTEM,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Assign a role to a user"""
        
        try:
            # Check if assignment already exists
            existing = await self.db.execute(
                select(UserRoleAssignment)
                .where(
                    and_(
                        UserRoleAssignment.user_id == user_id,
                        UserRoleAssignment.role == role,
                        UserRoleAssignment.client_id == client_id,
                        UserRoleAssignment.is_active == True
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                logger.warning(f"Role assignment already exists: user={user_id}, role={role}, client={client_id}")
                return False
            
            # Create new role assignment
            assignment = UserRoleAssignment(
                user_id=user_id,
                role=role,
                client_id=client_id,
                scope=scope,
                assigned_by_id=assigned_by_id,
                expires_at=expires_at
            )
            
            self.db.add(assignment)
            await self.db.commit()
            
            # Clear user's permission cache
            self._clear_user_cache(user_id)
            
            logger.info(f"Role {role} assigned to user {user_id} by {assigned_by_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning role {role} to user {user_id}: {e}")
            await self.db.rollback()
            return False
    
    async def revoke_role_from_user(
        self,
        user_id: int,
        role: UserRole,
        revoked_by_id: int,
        client_id: Optional[int] = None,
        reason: str = "Manual revocation"
    ) -> bool:
        """Revoke a role from a user"""
        
        try:
            # Find the role assignment
            result = await self.db.execute(
                select(UserRoleAssignment)
                .where(
                    and_(
                        UserRoleAssignment.user_id == user_id,
                        UserRoleAssignment.role == role,
                        UserRoleAssignment.client_id == client_id,
                        UserRoleAssignment.is_active == True
                    )
                )
            )
            
            assignment = result.scalar_one_or_none()
            if not assignment:
                logger.warning(f"Role assignment not found: user={user_id}, role={role}, client={client_id}")
                return False
            
            # Revoke the assignment
            if assignment.revoke_assignment(revoked_by_id, reason):
                await self.db.commit()
                
                # Clear user's permission cache
                self._clear_user_cache(user_id)
                
                logger.info(f"Role {role} revoked from user {user_id} by {revoked_by_id}: {reason}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking role {role} from user {user_id}: {e}")
            await self.db.rollback()
            return False
    
    async def grant_permission_override(
        self,
        user_id: int,
        permission: Permission,
        granted_by_id: int,
        is_granted: bool = True,
        client_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        scope: PermissionScope = PermissionScope.SYSTEM,
        context: PermissionContext = PermissionContext.ALL,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Grant or deny a specific permission to a user"""
        
        try:
            # Create permission override
            override = UserPermissionOverride(
                user_id=user_id,
                permission=permission,
                is_granted=is_granted,
                scope=scope,
                context=context,
                client_id=client_id,
                resource_id=resource_id,
                granted_by_id=granted_by_id,
                expires_at=expires_at,
                reason=reason
            )
            
            self.db.add(override)
            await self.db.commit()
            
            # Clear user's permission cache
            self._clear_user_cache(user_id)
            
            action = "granted" if is_granted else "denied"
            logger.info(f"Permission {permission} {action} for user {user_id} by {granted_by_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating permission override for user {user_id}: {e}")
            await self.db.rollback()
            return False
    
    # ==================== QUERY METHODS ====================
    
    async def get_user_permissions(
        self,
        user_id: int,
        client_id: Optional[int] = None,
        include_inherited: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all permissions for a user"""
        
        try:
            user = await self._get_user_with_permissions(user_id)
            if not user:
                return []
            
            permissions = []
            
            # Get role-based permissions
            valid_roles = self._get_valid_user_roles(user, client_id)
            
            for role, role_client_id in valid_roles:
                role_permissions = await self._get_role_permissions(role)
                
                for perm_data in role_permissions:
                    permissions.append({
                        "permission": perm_data["permission"].value,
                        "source": "role",
                        "source_detail": role.value,
                        "scope": perm_data["scope"].value,
                        "context": perm_data["context"].value,
                        "client_id": role_client_id
                    })
            
            # Get permission overrides
            for override in user.permission_overrides:
                if override.is_valid and (client_id is None or override.client_id == client_id):
                    permissions.append({
                        "permission": override.permission.value,
                        "source": "override",
                        "source_detail": "granted" if override.is_granted else "denied",
                        "scope": override.scope.value,
                        "context": override.context.value,
                        "client_id": override.client_id,
                        "resource_id": override.resource_id,
                        "expires_at": override.expires_at.isoformat() if override.expires_at else None
                    })
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {e}")
            return []
    
    async def _get_role_permissions(self, role: UserRole) -> List[Dict[str, Any]]:
        """Get all permissions for a role"""
        
        try:
            result = await self.db.execute(
                select(RolePermission)
                .where(
                    and_(
                        RolePermission.role == role,
                        RolePermission.is_active == True
                    )
                )
            )
            
            permissions = []
            for role_perm in result.scalars().all():
                permissions.append({
                    "permission": role_perm.permission,
                    "scope": role_perm.scope,
                    "context": role_perm.context
                })
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting permissions for role {role}: {e}")
            return []
    
    async def get_user_roles(
        self,
        user_id: int,
        client_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all roles for a user"""
        
        try:
            user = await self._get_user_with_permissions(user_id)
            if not user:
                return []
            
            roles = []
            
            # Add primary role
            roles.append({
                "role": user.role.value,
                "source": "primary",
                "client_id": None,
                "assigned_at": user.created_at.isoformat(),
                "expires_at": None
            })
            
            # Add role assignments
            for assignment in user.role_assignments:
                if assignment.is_valid and (client_id is None or assignment.client_id == client_id):
                    roles.append({
                        "role": assignment.role.value,
                        "source": "assignment",
                        "client_id": assignment.client_id,
                        "assigned_at": assignment.assigned_at.isoformat(),
                        "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None
                    })
            
            return roles
            
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {e}")
            return []
    
    # ==================== CACHING SYSTEM ====================
    
    def _generate_cache_key(
        self,
        user_id: int,
        permission: Permission,
        resource_id: Optional[str] = None,
        client_id: Optional[int] = None,
        context: Optional[PermissionContext] = None
    ) -> str:
        """Generate cache key for permission check"""
        
        parts = [
            f"user:{user_id}",
            f"perm:{permission.value}",
            f"resource:{resource_id or 'none'}",
            f"client:{client_id or 'none'}",
            f"context:{context.value if context else 'none'}"
        ]
        
        return "|".join(parts)
    
    def _get_cached_permission(self, cache_key: str) -> Optional[bool]:
        """Get cached permission result"""
        
        if cache_key not in self._permission_cache:
            return None
        
        cached_data = self._permission_cache[cache_key]
        
        # Check if cache is expired
        if datetime.utcnow() > cached_data["expires_at"]:
            del self._permission_cache[cache_key]
            return None
        
        return cached_data["result"]
    
    def _cache_permission(self, cache_key: str, result: bool) -> None:
        """Cache permission result"""
        
        self._permission_cache[cache_key] = {
            "result": result,
            "expires_at": datetime.utcnow() + self._cache_ttl
        }
    
    def _clear_user_cache(self, user_id: int) -> None:
        """Clear all cached permissions for a user"""
        
        keys_to_delete = []
        user_prefix = f"user:{user_id}|"
        
        for cache_key in self._permission_cache:
            if cache_key.startswith(user_prefix):
                keys_to_delete.append(cache_key)
        
        for key in keys_to_delete:
            del self._permission_cache[key]
    
    def clear_all_cache(self) -> None:
        """Clear all cached permissions"""
        self._permission_cache.clear()
    
    # ==================== UTILITY METHODS ====================
    
    async def validate_role_assignment(
        self,
        assigner_user_id: int,
        target_user_id: int,
        role: UserRole,
        client_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Validate if a user can assign a role to another user"""
        
        try:
            # Check if assigner has USER_ASSIGN_ROLE permission
            can_assign = await self.check_permission(
                assigner_user_id,
                Permission.USER_ASSIGN_ROLE,
                client_id=client_id
            )
            
            if not can_assign:
                return False, "Insufficient permissions to assign roles"
            
            # Get assigner's highest role
            assigner = await self._get_user_with_permissions(assigner_user_id)
            if not assigner:
                return False, "Assigner user not found"
            
            assigner_roles = self._get_valid_user_roles(assigner, client_id)
            if not assigner_roles:
                return False, "Assigner has no valid roles"
            
            highest_assigner_role = assigner_roles[0][0]  # Already sorted by hierarchy
            
            # Check if assigner can manage the target role
            if not highest_assigner_role.can_manage(role):
                return False, f"Cannot assign role {role.value} - insufficient hierarchy level"
            
            return True, "Role assignment validation passed"
            
        except Exception as e:
            logger.error(f"Error validating role assignment: {e}")
            return False, "Validation error occurred"
    
    @lru_cache(maxsize=100)
    def get_role_hierarchy_info(self) -> Dict[str, Any]:
        """Get role hierarchy information (cached)"""
        
        hierarchy = {}
        
        for role in UserRole:
            hierarchy[role.value] = {
                "level": UserRole.get_hierarchy_level(role),
                "can_manage": [
                    other_role.value 
                    for other_role in UserRole 
                    if role.can_manage(other_role)
                ],
                "inherits_from": [
                    other_role.value 
                    for other_role in UserRole 
                    if role.inherits_from(other_role) and role != other_role
                ]
            }
        
        return hierarchy


# ==================== RBAC DECORATORS ====================

def require_permission(permission: Union[Permission, str], client_context: bool = False):
    """Decorator to require specific permission for endpoint access"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (added by auth middleware)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise AuthorizationError("Authentication required")
            
            # Extract client_id if needed
            client_id = None
            if client_context:
                client_id = kwargs.get('client_id') or kwargs.get('id')  # Common patterns
            
            # Get RBAC service from dependency injection or create new instance
            db = kwargs.get('db')  # Assume db session is injected
            if not db:
                raise AuthorizationError("Database session required")
            
            rbac_service = RBACService(db)
            
            # Check permission
            has_permission = await rbac_service.check_permission(
                current_user['user_id'],
                permission,
                client_id=client_id
            )
            
            if not has_permission:
                perm_str = permission.value if isinstance(permission, Permission) else permission
                raise AuthorizationError(f"Permission denied: {perm_str}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: UserRole, client_context: bool = False):
    """Decorator to require specific role for endpoint access"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise AuthorizationError("Authentication required")
            
            # Simple role check from JWT token
            user_role = current_user.get('role')
            if not user_role:
                raise AuthorizationError("User role not found")
            
            try:
                user_role_enum = UserRole(user_role)
                if not user_role_enum.inherits_from(role):
                    raise AuthorizationError(f"Role required: {role.value}")
            except ValueError:
                raise AuthorizationError("Invalid user role")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator