"""
Permission management service
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError, AuthorizationError, GoogleAPIError
from ..models.db_models import (
    PermissionGrant, User, Client, ServiceAccount, 
    PermissionLevel, PermissionStatus, UserRole
)
from ..models.schemas import PermissionGrantCreate, PermissionGrantUpdate, PermissionGrantResponse
from ..services.google_api_service import GoogleAnalyticsService
from ..services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class PermissionService:
    """Permission management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ga_service = GoogleAnalyticsService()
        self.audit_service = AuditService(db)
    
    async def create_permission_request(
        self,
        user_id: int,
        grant_data: PermissionGrantCreate
    ) -> PermissionGrantResponse:
        """Create a new permission request"""
        
        # Validate user exists
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        # Validate client and service account exist
        client_result = await self.db.execute(select(Client).where(Client.id == grant_data.client_id))
        client = client_result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client not found")
        
        sa_result = await self.db.execute(
            select(ServiceAccount).where(ServiceAccount.id == grant_data.service_account_id)
        )
        service_account = sa_result.scalar_one_or_none()
        if not service_account:
            raise NotFoundError("Service account not found")
        
        # Check if there's already an active request for this combination
        existing_result = await self.db.execute(
            select(PermissionGrant).where(
                and_(
                    PermissionGrant.user_id == user_id,
                    PermissionGrant.client_id == grant_data.client_id,
                    PermissionGrant.ga_property_id == grant_data.ga_property_id,
                    PermissionGrant.target_email == grant_data.target_email,
                    PermissionGrant.status.in_([PermissionStatus.PENDING, PermissionStatus.APPROVED])
                )
            )
        )
        existing_grant = existing_result.scalar_one_or_none()
        
        if existing_grant:
            raise ValidationError("An active permission request already exists for this configuration")
        
        # Determine default expiration (30 days for viewer/analyst, manual for editor/admin)
        expires_at = grant_data.expires_at
        if not expires_at and grant_data.permission_level in [PermissionLevel.VIEWER, PermissionLevel.ANALYST]:
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Create permission grant
        permission_grant = PermissionGrant(
            user_id=user_id,
            client_id=grant_data.client_id,
            service_account_id=grant_data.service_account_id,
            ga_property_id=grant_data.ga_property_id,
            target_email=grant_data.target_email,
            permission_level=grant_data.permission_level,
            reason=grant_data.reason,
            expires_at=expires_at,
            status=PermissionStatus.PENDING
        )
        
        self.db.add(permission_grant)
        await self.db.commit()
        await self.db.refresh(permission_grant)
        
        # Log the creation
        await self.audit_service.log_action(
            actor_id=user_id,
            action="create_permission_request",
            resource_type="permission_grant",
            resource_id=str(permission_grant.id),
            details=f"Requested {grant_data.permission_level.value} access to property {grant_data.ga_property_id}"
        )
        
        return PermissionGrantResponse.model_validate(permission_grant)
    
    async def approve_permission_request(
        self,
        grant_id: int,
        approver_id: int,
        notes: Optional[str] = None
    ) -> PermissionGrantResponse:
        """Approve a permission request and grant actual GA4 access"""
        
        # Get the permission grant
        result = await self.db.execute(
            select(PermissionGrant)
            .options(selectinload(PermissionGrant.user))
            .where(PermissionGrant.id == grant_id)
        )
        grant = result.scalar_one_or_none()
        
        if not grant:
            raise NotFoundError("Permission grant not found")
        
        if grant.status != PermissionStatus.PENDING:
            raise ValidationError("Permission request is not in pending status")
        
        # Validate approver permissions
        approver_result = await self.db.execute(select(User).where(User.id == approver_id))
        approver = approver_result.scalar_one_or_none()
        if not approver:
            raise NotFoundError("Approver not found")
        
        if approver.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to approve requests")
        
        try:
            # Grant actual GA4 access
            property_name = f"properties/{grant.ga_property_id}"
            ga_result = await self.ga_service.grant_property_access(
                property_name=property_name,
                email_address=grant.target_email,
                permission_level=grant.permission_level
            )
            
            # Update the grant status
            grant.status = PermissionStatus.APPROVED
            grant.approved_at = datetime.utcnow()
            grant.approved_by_id = approver_id
            if notes:
                grant.notes = notes
            
            await self.db.commit()
            await self.db.refresh(grant)
            
            # Log the approval
            await self.audit_service.log_action(
                actor_id=approver_id,
                action="approve_permission_request",
                resource_type="permission_grant",
                resource_id=str(grant.id),
                details=f"Approved {grant.permission_level.value} access for {grant.target_email}"
            )
            
            logger.info(f"Successfully approved permission grant {grant_id}")
            
        except GoogleAPIError as e:
            # Update grant status to show GA4 error
            grant.status = PermissionStatus.PENDING
            grant.notes = f"GA4 API Error: {e.message}"
            await self.db.commit()
            
            logger.error(f"Failed to grant GA4 access for grant {grant_id}: {e}")
            raise GoogleAPIError(f"Failed to grant GA4 access: {e.message}")
        
        return PermissionGrantResponse.model_validate(grant)
    
    async def reject_permission_request(
        self,
        grant_id: int,
        rejector_id: int,
        reason: Optional[str] = None
    ) -> PermissionGrantResponse:
        """Reject a permission request"""
        
        # Get the permission grant
        result = await self.db.execute(select(PermissionGrant).where(PermissionGrant.id == grant_id))
        grant = result.scalar_one_or_none()
        
        if not grant:
            raise NotFoundError("Permission grant not found")
        
        if grant.status != PermissionStatus.PENDING:
            raise ValidationError("Permission request is not in pending status")
        
        # Validate rejector permissions
        rejector_result = await self.db.execute(select(User).where(User.id == rejector_id))
        rejector = rejector_result.scalar_one_or_none()
        if not rejector:
            raise NotFoundError("Rejector not found")
        
        if rejector.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to reject requests")
        
        # Update the grant status
        grant.status = PermissionStatus.REJECTED
        grant.approved_by_id = rejector_id
        if reason:
            grant.notes = reason
        
        await self.db.commit()
        await self.db.refresh(grant)
        
        # Log the rejection
        await self.audit_service.log_action(
            actor_id=rejector_id,
            action="reject_permission_request",
            resource_type="permission_grant",
            resource_id=str(grant.id),
            details=f"Rejected {grant.permission_level.value} access request"
        )
        
        return PermissionGrantResponse.model_validate(grant)
    
    async def revoke_permission(
        self,
        grant_id: int,
        revoker_id: int,
        reason: Optional[str] = None
    ) -> PermissionGrantResponse:
        """Revoke an active permission"""
        
        # Get the permission grant
        result = await self.db.execute(select(PermissionGrant).where(PermissionGrant.id == grant_id))
        grant = result.scalar_one_or_none()
        
        if not grant:
            raise NotFoundError("Permission grant not found")
        
        if grant.status != PermissionStatus.APPROVED:
            raise ValidationError("Permission is not in approved status")
        
        # Validate revoker permissions
        revoker_result = await self.db.execute(select(User).where(User.id == revoker_id))
        revoker = revoker_result.scalar_one_or_none()
        if not revoker:
            raise NotFoundError("Revoker not found")
        
        if revoker.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to revoke access")
        
        try:
            # Revoke actual GA4 access
            property_name = f"properties/{grant.ga_property_id}"
            await self.ga_service.revoke_property_access(
                property_name=property_name,
                email_address=grant.target_email
            )
            
            # Update the grant status
            grant.status = PermissionStatus.REVOKED
            if reason:
                grant.notes = f"{grant.notes or ''}\nRevoked: {reason}".strip()
            
            await self.db.commit()
            await self.db.refresh(grant)
            
            # Log the revocation
            await self.audit_service.log_action(
                actor_id=revoker_id,
                action="revoke_permission",
                resource_type="permission_grant",
                resource_id=str(grant.id),
                details=f"Revoked {grant.permission_level.value} access for {grant.target_email}"
            )
            
            logger.info(f"Successfully revoked permission grant {grant_id}")
            
        except GoogleAPIError as e:
            logger.error(f"Failed to revoke GA4 access for grant {grant_id}: {e}")
            # Still update status but add error note
            grant.notes = f"{grant.notes or ''}\nGA4 revocation failed: {e.message}".strip()
            await self.db.commit()
            
        return PermissionGrantResponse.model_validate(grant)
    
    async def extend_permission(
        self,
        grant_id: int,
        new_expiry: datetime,
        extender_id: Optional[int] = None
    ) -> PermissionGrantResponse:
        """Extend permission expiry date"""
        
        # Get the permission grant
        result = await self.db.execute(select(PermissionGrant).where(PermissionGrant.id == grant_id))
        grant = result.scalar_one_or_none()
        
        if not grant:
            raise NotFoundError("Permission grant not found")
        
        if grant.status != PermissionStatus.APPROVED:
            raise ValidationError("Permission is not in approved status")
        
        # Update expiry date
        old_expiry = grant.expires_at
        grant.expires_at = new_expiry
        
        await self.db.commit()
        await self.db.refresh(grant)
        
        # Log the extension
        if extender_id:
            await self.audit_service.log_action(
                actor_id=extender_id,
                action="extend_permission",
                resource_type="permission_grant",
                resource_id=str(grant.id),
                details=f"Extended expiry from {old_expiry} to {new_expiry}"
            )
        
        return PermissionGrantResponse.model_validate(grant)
    
    async def list_permission_grants(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        client_id: Optional[int] = None,
        status: Optional[PermissionStatus] = None
    ) -> List[PermissionGrantResponse]:
        """List permission grants with optional filters"""
        
        query = select(PermissionGrant).options(
            selectinload(PermissionGrant.user),
            selectinload(PermissionGrant.client),
            selectinload(PermissionGrant.service_account)
        )
        
        if user_id:
            query = query.where(PermissionGrant.user_id == user_id)
        if client_id:
            query = query.where(PermissionGrant.client_id == client_id)
        if status:
            query = query.where(PermissionGrant.status == status)
        
        query = query.offset(skip).limit(limit).order_by(PermissionGrant.created_at.desc())
        
        result = await self.db.execute(query)
        grants = result.scalars().all()
        
        return [PermissionGrantResponse.model_validate(grant) for grant in grants]
    
    async def get_permission_grant(self, grant_id: int) -> Optional[PermissionGrantResponse]:
        """Get permission grant by ID"""
        
        result = await self.db.execute(
            select(PermissionGrant)
            .options(
                selectinload(PermissionGrant.user),
                selectinload(PermissionGrant.client),
                selectinload(PermissionGrant.service_account)
            )
            .where(PermissionGrant.id == grant_id)
        )
        grant = result.scalar_one_or_none()
        
        if not grant:
            return None
        
        return PermissionGrantResponse.model_validate(grant)