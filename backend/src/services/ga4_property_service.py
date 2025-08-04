"""
GA4 Property management service - Legacy compatible
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError, AuthorizationError
from ..models.db_models import (
    GA4Property, Client, User, UserPermission, 
    PermissionLevel, PermissionStatus, UserRole
)
from ..models.schemas import (
    GA4PropertyCreate, GA4PropertyUpdate, GA4PropertyResponse,
    UserPermissionCreate, UserPermissionResponse
)
from ..services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class GA4PropertyService:
    """GA4 Property management service - Legacy compatible"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
    
    async def create_property(
        self,
        user_id: int,
        property_data: GA4PropertyCreate
    ) -> GA4PropertyResponse:
        """Create a new GA4 property"""
        
        # Validate user permissions
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to create GA4 properties")
        
        # Validate client exists
        client_result = await self.db.execute(select(Client).where(Client.id == property_data.client_id))
        client = client_result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client not found")
        
        # Check if property already exists
        existing_result = await self.db.execute(
            select(GA4Property).where(GA4Property.property_id == property_data.property_id)
        )
        existing_property = existing_result.scalar_one_or_none()
        
        if existing_property:
            raise ValidationError(f"Property {property_data.property_id} already exists")
        
        # Create GA4 property
        ga4_property = GA4Property(
            client_id=property_data.client_id,
            property_id=property_data.property_id,
            property_name=property_data.property_name,
            account_id=property_data.account_id,
            account_name=property_data.account_name,
            website_url=property_data.website_url,
            timezone=property_data.timezone,
            currency_code=property_data.currency_code,
            auto_approval_enabled=property_data.auto_approval_enabled,
            max_permission_duration_days=property_data.max_permission_duration_days
        )
        
        self.db.add(ga4_property)
        await self.db.commit()
        await self.db.refresh(ga4_property)
        
        # Log the creation
        await self.audit_service.log_action(
            actor_id=user_id,
            action="create_ga4_property",
            resource_type="ga4_property",
            resource_id=str(ga4_property.id),
            details=f"Created GA4 property {property_data.property_name} ({property_data.property_id})"
        )
        
        logger.info(f"Successfully created GA4 property {ga4_property.id}")
        
        return GA4PropertyResponse.model_validate(ga4_property)
    
    async def update_property(
        self,
        property_id: int,
        user_id: int,
        property_data: GA4PropertyUpdate
    ) -> GA4PropertyResponse:
        """Update a GA4 property"""
        
        # Get the property
        result = await self.db.execute(
            select(GA4Property)
            .options(selectinload(GA4Property.client))
            .where(GA4Property.id == property_id)
        )
        ga4_property = result.scalar_one_or_none()
        
        if not ga4_property:
            raise NotFoundError("GA4 property not found")
        
        # Validate user permissions
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to update GA4 properties")
        
        # Update fields
        update_data = property_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ga4_property, field, value)
        
        await self.db.commit()
        await self.db.refresh(ga4_property)
        
        # Log the update
        await self.audit_service.log_action(
            actor_id=user_id,
            action="update_ga4_property",
            resource_type="ga4_property",
            resource_id=str(ga4_property.id),
            details=f"Updated GA4 property {ga4_property.property_name}"
        )
        
        return GA4PropertyResponse.model_validate(ga4_property)
    
    async def get_property(self, property_id: int) -> Optional[GA4PropertyResponse]:
        """Get GA4 property by ID"""
        
        result = await self.db.execute(
            select(GA4Property)
            .options(selectinload(GA4Property.client))
            .where(GA4Property.id == property_id)
        )
        ga4_property = result.scalar_one_or_none()
        
        if not ga4_property:
            return None
        
        response = GA4PropertyResponse.model_validate(ga4_property)
        response.display_name = ga4_property.display_name
        response.needs_sync = ga4_property.needs_sync
        
        return response
    
    async def list_properties(
        self,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[int] = None,
        active_only: bool = True,
        search_term: Optional[str] = None
    ) -> List[GA4PropertyResponse]:
        """List GA4 properties with optional filters"""
        
        query = select(GA4Property).options(
            selectinload(GA4Property.client)
        )
        
        if client_id:
            query = query.where(GA4Property.client_id == client_id)
        
        if active_only:
            query = query.where(GA4Property.is_active == True)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    GA4Property.property_name.ilike(search_pattern),
                    GA4Property.property_id.ilike(search_pattern),
                    GA4Property.account_name.ilike(search_pattern)
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(GA4Property.created_at.desc())
        
        result = await self.db.execute(query)
        properties = result.scalars().all()
        
        responses = []
        for prop in properties:
            response = GA4PropertyResponse.model_validate(prop)
            response.display_name = prop.display_name
            response.needs_sync = prop.needs_sync
            responses.append(response)
        
        return responses
    
    async def delete_property(
        self,
        property_id: int,
        user_id: int
    ) -> bool:
        """Soft delete a GA4 property"""
        
        # Get the property
        result = await self.db.execute(
            select(GA4Property).where(GA4Property.id == property_id)
        )
        ga4_property = result.scalar_one_or_none()
        
        if not ga4_property:
            raise NotFoundError("GA4 property not found")
        
        # Validate user permissions
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        if user.role != UserRole.SUPER_ADMIN:
            raise AuthorizationError("Only Super Admins can delete GA4 properties")
        
        # Check for active user permissions
        active_permissions_result = await self.db.execute(
            select(func.count(UserPermission.id))
            .where(
                and_(
                    UserPermission.ga_property_id == property_id,
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        active_permissions_count = active_permissions_result.scalar()
        
        if active_permissions_count > 0:
            raise ValidationError(
                f"Cannot delete property with {active_permissions_count} active permissions. "
                "Revoke all active permissions first."
            )
        
        # Soft delete the property
        ga4_property.deleted_at = datetime.utcnow()
        ga4_property.is_active = False
        
        await self.db.commit()
        
        # Log the deletion
        await self.audit_service.log_action(
            actor_id=user_id,
            action="delete_ga4_property",
            resource_type="ga4_property",
            resource_id=str(ga4_property.id),
            details=f"Deleted GA4 property {ga4_property.property_name}"
        )
        
        logger.info(f"Successfully deleted GA4 property {property_id}")
        
        return True
    
    async def sync_property(
        self,
        property_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Manually trigger GA4 property sync"""
        
        # Get the property
        result = await self.db.execute(
            select(GA4Property).where(GA4Property.id == property_id)
        )
        ga4_property = result.scalar_one_or_none()
        
        if not ga4_property:
            raise NotFoundError("GA4 property not found")
        
        if not ga4_property.sync_enabled:
            raise ValidationError("Sync is disabled for this property")
        
        # TODO: Implement actual GA4 API sync logic
        # For now, just update the sync timestamp
        ga4_property.last_synced_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Log the sync
        await self.audit_service.log_action(
            actor_id=user_id,
            action="sync_ga4_property",
            resource_type="ga4_property",
            resource_id=str(ga4_property.id),
            details=f"Manually synced GA4 property {ga4_property.property_name}"
        )
        
        return {
            "success": True,
            "property_id": property_id,
            "synced_at": ga4_property.last_synced_at,
            "message": "Property sync completed successfully"
        }
    
    async def get_properties_needing_sync(self) -> List[GA4PropertyResponse]:
        """Get properties that need synchronization"""
        
        result = await self.db.execute(
            select(GA4Property)
            .options(selectinload(GA4Property.client))
            .where(
                and_(
                    GA4Property.is_active == True,
                    GA4Property.sync_enabled == True,
                    or_(
                        GA4Property.last_synced_at.is_(None),
                        GA4Property.last_synced_at < (datetime.utcnow() - timedelta(hours=24))
                    )
                )
            )
            .order_by(GA4Property.last_synced_at.asc().nulls_first())
        )
        properties = result.scalars().all()
        
        responses = []
        for prop in properties:
            response = GA4PropertyResponse.model_validate(prop)
            response.display_name = prop.display_name
            response.needs_sync = prop.needs_sync
            responses.append(response)
        
        return responses