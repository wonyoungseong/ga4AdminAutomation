"""
User Permission management service - Legacy compatible
Handles direct user-property permission mappings
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError, AuthorizationError, GoogleAPIError
from ..models.db_models import (
    UserPermission, User, GA4Property, Client,
    PermissionLevel, PermissionStatus, UserRole
)
from ..models.schemas import (
    UserPermissionCreate, UserPermissionResponse,
    PermissionExtensionRequest, PermissionRevocationRequest
)
from ..services.google_api_service import GoogleAnalyticsService
from ..services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class UserPermissionService:
    """User Permission management service - Legacy compatible"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ga_service = GoogleAnalyticsService()
        self.audit_service = AuditService(db)
    
    async def create_user_permission(
        self,
        creator_id: int,
        permission_data: UserPermissionCreate
    ) -> UserPermissionResponse:
        """Create a new user permission"""
        
        # Validate creator permissions
        creator_result = await self.db.execute(select(User).where(User.id == creator_id))
        creator = creator_result.scalar_one_or_none()
        if not creator:
            raise NotFoundError("Creator not found")
        
        if creator.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to create user permissions")
        
        # Validate user exists
        user_result = await self.db.execute(select(User).where(User.id == permission_data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        # Validate GA4 property exists
        property_result = await self.db.execute(
            select(GA4Property)
            .options(selectinload(GA4Property.client))
            .where(GA4Property.id == permission_data.ga_property_id)
        )
        property_obj = property_result.scalar_one_or_none()
        if not property_obj:
            raise NotFoundError("GA4 property not found")
        
        # Check for existing active permission
        existing_result = await self.db.execute(
            select(UserPermission).where(
                and_(
                    UserPermission.user_id == permission_data.user_id,
                    UserPermission.ga_property_id == permission_data.ga_property_id,
                    UserPermission.target_email == permission_data.target_email,
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        existing_permission = existing_result.scalar_one_or_none()
        
        if existing_permission:
            raise ValidationError("An active permission already exists for this user and property")
        
        # Create user permission
        user_permission = UserPermission(
            user_id=permission_data.user_id,
            ga_property_id=permission_data.ga_property_id,
            target_email=permission_data.target_email,
            permission_level=permission_data.permission_level,
            expires_at=permission_data.expires_at,
            original_expires_at=permission_data.expires_at
        )
        
        self.db.add(user_permission)
        await self.db.commit()
        await self.db.refresh(user_permission)
        
        # Log the creation
        await self.audit_service.log_action(
            actor_id=creator_id,
            action="create_user_permission",
            resource_type="user_permission",
            resource_id=str(user_permission.id),
            details=f"Created {permission_data.permission_level.value} permission for {permission_data.target_email}"
        )
        
        logger.info(f"Successfully created user permission {user_permission.id}")
        
        return UserPermissionResponse.model_validate(user_permission)
    
    async def extend_permission(
        self,
        permission_id: int,
        extender_id: int,
        extension_request: PermissionExtensionRequest
    ) -> UserPermissionResponse:
        """Extend a user permission"""
        
        # Get the permission
        result = await self.db.execute(
            select(UserPermission)
            .options(
                selectinload(UserPermission.user),
                selectinload(UserPermission.ga_property)
            )
            .where(UserPermission.id == permission_id)
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise NotFoundError("User permission not found")
        
        # Validate extender permissions
        extender_result = await self.db.execute(select(User).where(User.id == extender_id))
        extender = extender_result.scalar_one_or_none()
        if not extender:
            raise NotFoundError("Extender not found")
        
        if extender.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to extend permissions")
        
        # Check if permission can be extended
        if not permission.is_active:
            raise ValidationError("Permission is not active and cannot be extended")
        
        if permission.extension_count >= 3:
            raise ValidationError("Maximum number of extensions (3) reached")
        
        # Extend the permission
        success = permission.extend_permission(extension_request.additional_days, extender_id)
        if not success:
            raise ValidationError("Failed to extend permission")
        
        await self.db.commit()
        await self.db.refresh(permission)
        
        # Log the extension
        await self.audit_service.log_action(
            actor_id=extender_id,
            action="extend_user_permission",
            resource_type="user_permission",
            resource_id=str(permission.id),
            details=f"Extended permission by {extension_request.additional_days} days. Reason: {extension_request.reason}"
        )
        
        logger.info(f"Successfully extended user permission {permission_id}")
        
        return UserPermissionResponse.model_validate(permission)
    
    async def revoke_permission(
        self,
        permission_id: int,
        revoker_id: int,
        revocation_request: PermissionRevocationRequest
    ) -> UserPermissionResponse:
        """Revoke a user permission"""
        
        # Get the permission
        result = await self.db.execute(
            select(UserPermission)
            .options(
                selectinload(UserPermission.user),
                selectinload(UserPermission.ga_property)
            )
            .where(UserPermission.id == permission_id)
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            raise NotFoundError("User permission not found")
        
        # Validate revoker permissions
        revoker_result = await self.db.execute(select(User).where(User.id == revoker_id))
        revoker = revoker_result.scalar_one_or_none()
        if not revoker:
            raise NotFoundError("Revoker not found")
        
        if revoker.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to revoke permissions")
        
        try:
            # Revoke actual GA4 access if immediate
            if revocation_request.immediate and permission.google_permission_id:
                property_name = f"properties/{permission.ga_property.property_id}"
                await self.ga_service.revoke_property_access(
                    property_name=property_name,
                    email_address=permission.target_email
                )
            
            # Revoke the permission
            success = permission.revoke_permission(revoker_id, revocation_request.reason)
            if not success:
                raise ValidationError("Failed to revoke permission")
            
            await self.db.commit()
            await self.db.refresh(permission)
            
            # Log the revocation
            await self.audit_service.log_action(
                actor_id=revoker_id,
                action="revoke_user_permission",
                resource_type="user_permission",
                resource_id=str(permission.id),
                details=f"Revoked permission. Reason: {revocation_request.reason}"
            )
            
            logger.info(f"Successfully revoked user permission {permission_id}")
            
        except GoogleAPIError as e:
            logger.error(f"Failed to revoke GA4 access for permission {permission_id}: {e}")
            # Still revoke locally but add error note
            success = permission.revoke_permission(revoker_id, f"{revocation_request.reason} (GA4 revocation failed: {e.message})")
            await self.db.commit()
            
        return UserPermissionResponse.model_validate(permission)
    
    async def get_user_permission(self, permission_id: int) -> Optional[UserPermissionResponse]:
        """Get user permission by ID"""
        
        result = await self.db.execute(
            select(UserPermission)
            .options(
                selectinload(UserPermission.user),
                selectinload(UserPermission.ga_property),
                selectinload(UserPermission.revoked_by)
            )
            .where(UserPermission.id == permission_id)
        )
        permission = result.scalar_one_or_none()
        
        if not permission:
            return None
        
        response = UserPermissionResponse.model_validate(permission)
        response.is_active = permission.is_active
        response.days_until_expiry = permission.days_until_expiry
        response.is_expiring_soon = permission.is_expiring_soon
        
        return response
    
    async def list_user_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        ga_property_id: Optional[int] = None,
        status: Optional[PermissionStatus] = None,
        expiring_within_days: Optional[int] = None
    ) -> List[UserPermissionResponse]:
        """List user permissions with optional filters"""
        
        query = select(UserPermission).options(
            selectinload(UserPermission.user),
            selectinload(UserPermission.ga_property),
            selectinload(UserPermission.revoked_by)
        )
        
        if user_id:
            query = query.where(UserPermission.user_id == user_id)
        
        if ga_property_id:
            query = query.where(UserPermission.ga_property_id == ga_property_id)
        
        if status:
            query = query.where(UserPermission.status == status)
        
        if expiring_within_days is not None:
            expiry_threshold = datetime.utcnow() + timedelta(days=expiring_within_days)
            query = query.where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= expiry_threshold,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(UserPermission.created_at.desc())
        
        result = await self.db.execute(query)
        permissions = result.scalars().all()
        
        responses = []
        for permission in permissions:
            response = UserPermissionResponse.model_validate(permission)
            response.is_active = permission.is_active
            response.days_until_expiry = permission.days_until_expiry
            response.is_expiring_soon = permission.is_expiring_soon
            responses.append(response)
        
        return responses
    
    async def get_expiring_permissions(
        self,
        days_ahead: int = 7
    ) -> List[UserPermissionResponse]:
        """Get permissions expiring within specified days"""
        
        expiry_threshold = datetime.utcnow() + timedelta(days=days_ahead)
        
        result = await self.db.execute(
            select(UserPermission)
            .options(
                selectinload(UserPermission.user),
                selectinload(UserPermission.ga_property)
            )
            .where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= expiry_threshold,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
            .order_by(UserPermission.expires_at.asc())
        )
        permissions = result.scalars().all()
        
        responses = []
        for permission in permissions:
            response = UserPermissionResponse.model_validate(permission)
            response.is_active = permission.is_active
            response.days_until_expiry = permission.days_until_expiry
            response.is_expiring_soon = permission.is_expiring_soon
            responses.append(response)
        
        return responses
    
    async def get_user_permissions_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get user permission summary"""
        
        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        # Get permission counts
        total_result = await self.db.execute(
            select(func.count(UserPermission.id))
            .where(UserPermission.user_id == user_id)
        )
        total_permissions = total_result.scalar()
        
        active_result = await self.db.execute(
            select(func.count(UserPermission.id))
            .where(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        active_permissions = active_result.scalar()
        
        expiring_result = await self.db.execute(
            select(func.count(UserPermission.id))
            .where(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= (datetime.utcnow() + timedelta(days=7)),
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        expiring_soon = expiring_result.scalar()
        
        extensions_result = await self.db.execute(
            select(func.sum(UserPermission.extension_count))
            .where(UserPermission.user_id == user_id)
        )
        total_extensions = extensions_result.scalar() or 0
        
        return {
            "user_id": user_id,
            "user_email": user.email,
            "user_name": user.name,
            "total_permissions": total_permissions,
            "active_permissions": active_permissions,
            "expiring_soon": expiring_soon,
            "total_extensions": total_extensions,
            "summary_generated_at": datetime.utcnow()
        }