"""
RBAC Middleware Integration

High-performance middleware that integrates RBAC with JWT authentication.
Provides automatic permission checking and role validation for protected endpoints.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any, Callable
import logging
import time
from functools import wraps

from ..core.database import get_db
from ..core.exceptions import AuthorizationError
from ..models.db_models import UserRole, Permission
from ..services.auth_service import AuthService
from ..services.rbac_service import RBACService

logger = logging.getLogger(__name__)
security = HTTPBearer()


class RBACMiddleware:
    """RBAC Middleware for FastAPI applications"""
    
    def __init__(self):
        self.rbac_cache: Dict[str, Dict] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
    
    async def __call__(self, request: Request, call_next):
        """Process request with RBAC validation"""
        
        start_time = time.time()
        
        try:
            # Skip RBAC for public endpoints
            if self._is_public_endpoint(request.url.path):
                response = await call_next(request)
                return response
            
            # Extract user from JWT token
            user_info = await self._extract_user_from_request(request)
            if not user_info:
                # Let auth middleware handle authentication
                response = await call_next(request)
                return response
            
            # Add user info to request state for downstream handlers
            request.state.current_user = user_info
            request.state.rbac_validated = True
            
            # Process the request
            response = await call_next(request)
            
            # Log performance metrics
            processing_time = time.time() - start_time
            self._log_performance_metric(request.url.path, processing_time)
            
            return response
            
        except AuthorizationError as e:
            logger.warning(f"Authorization failed for {request.url.path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"RBAC middleware error for {request.url.path}: {e}")
            # Don't block request on middleware errors
            response = await call_next(request)
            return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)"""
        public_paths = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/docs",
            "/openapi.json",
            "/health",
            "/api/health"
        ]
        
        # Check exact matches and prefix matches
        for public_path in public_paths:
            if path == public_path or path.startswith(public_path + "/"):
                return True
        
        return False
    
    async def _extract_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token in request"""
        
        try:
            # Get authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Verify token and extract user info
            payload = AuthService.verify_token(token)
            
            return {
                "user_id": payload.get("user_id"),
                "email": payload.get("sub"),
                "role": payload.get("role"),
                "token_payload": payload
            }
            
        except Exception as e:
            logger.debug(f"Failed to extract user from request: {e}")
            return None
    
    def _log_performance_metric(self, endpoint: str, processing_time: float):
        """Log performance metrics for RBAC operations"""
        
        if endpoint not in self.performance_metrics:
            self.performance_metrics[endpoint] = []
        
        # Keep only last 100 measurements per endpoint
        metrics = self.performance_metrics[endpoint]
        metrics.append(processing_time)
        if len(metrics) > 100:
            metrics.pop(0)
        
        # Log warning if processing time exceeds threshold (100ms)
        if processing_time > 0.1:
            logger.warning(f"RBAC processing time exceeded 100ms for {endpoint}: {processing_time:.3f}s")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        
        stats = {}
        
        for endpoint, metrics in self.performance_metrics.items():
            if metrics:
                stats[endpoint] = {
                    "avg_time": sum(metrics) / len(metrics),
                    "max_time": max(metrics),
                    "min_time": min(metrics),
                    "sample_count": len(metrics),
                    "last_time": metrics[-1]
                }
        
        return stats


# Global middleware instance
rbac_middleware = RBACMiddleware()


# ==================== PERMISSION DECORATORS ====================

def require_permission(
    permission: Permission,
    client_context: bool = False,
    resource_context: bool = False,
    fail_silently: bool = False
):
    """
    Decorator to require specific permission for endpoint access
    
    Args:
        permission: Required permission
        client_context: Extract client_id from request parameters
        resource_context: Extract resource_id from request parameters
        fail_silently: Return False instead of raising exception
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get database session and current user from kwargs
            db = None
            current_user = None
            
            # Find db and current_user in kwargs
            for key, value in kwargs.items():
                if isinstance(value, AsyncSession):
                    db = value
                elif isinstance(value, dict) and 'user_id' in value:
                    current_user = value
            
            # Try to get from request state if not in kwargs
            if not current_user:
                # This would work if request is available in context
                try:
                    from starlette.requests import Request
                    request = kwargs.get('request')
                    if request and hasattr(request.state, 'current_user'):
                        current_user = request.state.current_user
                except:
                    pass
            
            if not current_user:
                if fail_silently:
                    return False
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                if fail_silently:
                    return False
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Extract context from request parameters
            client_id = None
            resource_id = None
            
            if client_context:
                client_id = kwargs.get('client_id') or kwargs.get('id')
            
            if resource_context:
                resource_id = kwargs.get('resource_id') or kwargs.get('id')
            
            # Check permission
            rbac_service = RBACService(db)
            has_permission = await rbac_service.check_permission(
                user_id=current_user['user_id'],
                permission=permission,
                resource_id=str(resource_id) if resource_id else None,
                client_id=client_id
            )
            
            if not has_permission:
                if fail_silently:
                    return False
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(
    role: UserRole,
    client_context: bool = False,
    strict: bool = False
):
    """
    Decorator to require specific role for endpoint access
    
    Args:
        role: Required role (minimum level)
        client_context: Check role within client context
        strict: Require exact role match (no inheritance)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user
            current_user = None
            
            for key, value in kwargs.items():
                if isinstance(value, dict) and 'user_id' in value:
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get user role from token
            user_role_str = current_user.get('role')
            if not user_role_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User role not found"
                )
            
            try:
                user_role = UserRole(user_role_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid user role"
                )
            
            # Check role requirement
            if strict:
                # Exact role match required
                if user_role != role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role required: {role.value} (strict)"
                    )
            else:
                # Role inheritance allowed
                if not user_role.inherits_from(role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Minimum role required: {role.value}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def admin_required(func):
    """Shortcut decorator for admin-only endpoints"""
    return require_role(UserRole.ADMIN)(func)


def super_admin_required(func):
    """Shortcut decorator for super admin-only endpoints"""
    return require_role(UserRole.SUPER_ADMIN, strict=True)(func)


# ==================== DEPENDENCY INJECTION HELPERS ====================

async def get_current_user_with_permissions(
    current_user: Dict = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enhanced dependency that includes user permissions in the response
    
    Returns user info with additional RBAC context
    """
    try:
        rbac_service = RBACService(db)
        
        # Get user permissions
        permissions = await rbac_service.get_user_permissions(
            user_id=current_user["user_id"],
            include_inherited=True
        )
        
        # Get user roles
        roles = await rbac_service.get_user_roles(
            user_id=current_user["user_id"]
        )
        
        # Enhance user info with RBAC data
        enhanced_user = {
            **current_user,
            "permissions": permissions,
            "roles": roles,
            "rbac_loaded_at": time.time()
        }
        
        return enhanced_user
        
    except Exception as e:
        logger.error(f"Error loading RBAC data for user {current_user['user_id']}: {e}")
        # Return basic user info if RBAC loading fails
        return current_user


async def check_permission_dependency(
    permission: str,
    client_id: Optional[int] = None,
    resource_id: Optional[str] = None
):
    """
    Dependency factory for permission checking
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(
            can_access: bool = Depends(check_permission_dependency("user:create"))
        ):
            if not can_access:
                raise HTTPException(403, "Access denied")
    """
    async def _check_permission(
        current_user: Dict = Depends(AuthService.get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> bool:
        rbac_service = RBACService(db)
        
        return await rbac_service.check_permission(
            user_id=current_user["user_id"],
            permission=permission,
            resource_id=resource_id,
            client_id=client_id
        )
    
    return _check_permission


# ==================== PERFORMANCE MONITORING ====================

def get_rbac_performance_stats() -> Dict[str, Any]:
    """Get RBAC middleware performance statistics"""
    return rbac_middleware.get_performance_stats()


def clear_rbac_performance_stats():
    """Clear RBAC middleware performance statistics"""
    rbac_middleware.performance_metrics.clear()