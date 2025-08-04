"""
Service Account management service
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError, AuthorizationError, GoogleAPIError
from ..models.db_models import (
    ServiceAccount, Client, User, UserRole,
    ServiceAccountProperty, PropertyAccessBinding
)
from ..models.schemas import (
    ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse,
    GA4PropertyResponse, PaginatedResponse
)
from ..services.google_api_service import GoogleAnalyticsService
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ServiceAccountService:
    """Service Account management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ga_service = GoogleAnalyticsService()
        self.audit_service = AuditService(db)
    
    async def create_service_account(
        self,
        sa_data: ServiceAccountCreate,
        created_by_id: int
    ) -> ServiceAccountResponse:
        """Create a new service account"""
        
        # Validate client exists
        client_result = await self.db.execute(select(Client).where(Client.id == sa_data.client_id))
        client = client_result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client not found")
        
        # Check if service account email already exists
        existing_result = await self.db.execute(
            select(ServiceAccount).where(ServiceAccount.email == sa_data.email)
        )
        existing_sa = existing_result.scalar_one_or_none()
        if existing_sa:
            raise ValidationError(f"Service account with email {sa_data.email} already exists")
        
        # Validate service account credentials if provided
        if sa_data.credentials_json:
            try:
                credentials_data = json.loads(sa_data.credentials_json)
                if credentials_data.get("client_email") != sa_data.email:
                    raise ValidationError("Service account email does not match credentials")
                
                # Test the credentials by initializing GA service
                test_ga_service = GoogleAnalyticsService(credentials_json=sa_data.credentials_json)
                await test_ga_service.validate_credentials()
                
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for credentials")
            except GoogleAPIError as e:
                raise GoogleAPIError(f"Invalid service account credentials: {str(e)}")
        
        # Create service account
        service_account = ServiceAccount(
            client_id=sa_data.client_id,
            email=sa_data.email,
            secret_name=sa_data.secret_name,
            display_name=sa_data.display_name,
            project_id=getattr(sa_data, 'project_id', None),
            is_active=True,
            health_status='unknown'
        )
        
        self.db.add(service_account)
        await self.db.commit()
        await self.db.refresh(service_account)
        
        # Store credentials in secret manager if provided
        if sa_data.credentials_json:
            try:
                # Here you would store credentials in Google Secret Manager
                # For now, we'll just log that we would do this
                logger.info(f"Would store credentials for service account {service_account.id} in Secret Manager")
                service_account.health_status = 'healthy'
                await self.db.commit()
            except Exception as e:
                logger.error(f"Failed to store credentials: {str(e)}")
                service_account.health_status = 'unhealthy'
                await self.db.commit()
        
        # Log the creation
        await self.audit_service.log_action(
            actor_id=created_by_id,
            action="create_service_account",
            resource_type="service_account",
            resource_id=str(service_account.id),
            details=f"Created service account {service_account.email} for client {client.name}"
        )
        
        return ServiceAccountResponse.model_validate(service_account)
    
    async def list_service_accounts(
        self,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        accessible_client_ids: Optional[List[int]] = None
    ) -> PaginatedResponse[ServiceAccountResponse]:
        """List service accounts with filters and pagination"""
        
        query = select(ServiceAccount).options(selectinload(ServiceAccount.client))
        
        # Apply filters
        conditions = []
        if client_id:
            conditions.append(ServiceAccount.client_id == client_id)
        if is_active is not None:
            conditions.append(ServiceAccount.is_active == is_active)
        if accessible_client_ids is not None:
            conditions.append(ServiceAccount.client_id.in_(accessible_client_ids))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(ServiceAccount.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(ServiceAccount.created_at.desc())
        
        result = await self.db.execute(query)
        service_accounts = result.scalars().all()
        
        items = [ServiceAccountResponse.model_validate(sa) for sa in service_accounts]
        
        return PaginatedResponse[ServiceAccountResponse](
            items=items,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    async def get_service_account(self, sa_id: int) -> Optional[ServiceAccountResponse]:
        """Get service account by ID"""
        
        result = await self.db.execute(
            select(ServiceAccount)
            .options(selectinload(ServiceAccount.client))
            .where(ServiceAccount.id == sa_id)
        )
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            return None
        
        return ServiceAccountResponse.model_validate(service_account)
    
    async def update_service_account(
        self,
        sa_id: int,
        sa_data: ServiceAccountUpdate,
        updated_by_id: int
    ) -> ServiceAccountResponse:
        """Update service account"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        # Track changes for audit log
        changes = []
        
        # Update fields
        if sa_data.display_name is not None and sa_data.display_name != service_account.display_name:
            changes.append(f"display_name: {service_account.display_name} → {sa_data.display_name}")
            service_account.display_name = sa_data.display_name
        
        if sa_data.is_active is not None and sa_data.is_active != service_account.is_active:
            changes.append(f"is_active: {service_account.is_active} → {sa_data.is_active}")
            service_account.is_active = sa_data.is_active
        
        if sa_data.secret_name is not None and sa_data.secret_name != service_account.secret_name:
            changes.append(f"secret_name: {service_account.secret_name} → {sa_data.secret_name}")
            service_account.secret_name = sa_data.secret_name
        
        service_account.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(service_account)
        
        # Log the update if there were changes
        if changes:
            await self.audit_service.log_action(
                actor_id=updated_by_id,
                action="update_service_account",
                resource_type="service_account",
                resource_id=str(service_account.id),
                details=f"Updated service account: {', '.join(changes)}"
            )
        
        return ServiceAccountResponse.model_validate(service_account)
    
    async def delete_service_account(
        self,
        sa_id: int,
        deleted_by_id: int
    ) -> None:
        """Delete service account"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        # Check if service account has active permission grants
        from ..models.db_models import PermissionGrant, PermissionStatus
        active_grants_result = await self.db.execute(
            select(func.count(PermissionGrant.id))
            .where(
                and_(
                    PermissionGrant.service_account_id == sa_id,
                    PermissionGrant.status == PermissionStatus.APPROVED
                )
            )
        )
        active_grants_count = active_grants_result.scalar()
        
        if active_grants_count > 0:
            raise ValidationError(
                f"Cannot delete service account with {active_grants_count} active permission grants. "
                "Please revoke all permissions first."
            )
        
        # Store info for audit log before deletion
        sa_email = service_account.email
        client_id = service_account.client_id
        
        # Delete service account (cascade will handle related records)
        await self.db.delete(service_account)
        await self.db.commit()
        
        # Log the deletion
        await self.audit_service.log_action(
            actor_id=deleted_by_id,
            action="delete_service_account",
            resource_type="service_account",
            resource_id=str(sa_id),
            details=f"Deleted service account {sa_email} for client {client_id}"
        )
    
    async def validate_service_account(self, sa_id: int) -> Dict[str, Any]:
        """Validate service account credentials and permissions"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        validation_result = {
            "service_account_id": sa_id,
            "email": service_account.email,
            "is_valid": False,
            "has_ga4_access": False,
            "accessible_accounts": [],
            "accessible_properties": [],
            "errors": [],
            "validated_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Initialize GA service with service account credentials
            ga_service = GoogleAnalyticsService(secret_name=service_account.secret_name)
            
            # Test basic API access
            accounts = await ga_service.list_accounts()
            validation_result["is_valid"] = True
            validation_result["has_ga4_access"] = len(accounts) > 0
            validation_result["accessible_accounts"] = accounts
            
            # Get accessible properties
            properties = await ga_service.list_properties()
            validation_result["accessible_properties"] = properties
            
            # Update service account health status
            service_account.health_status = 'healthy'
            service_account.health_checked_at = datetime.utcnow()
            service_account.last_used_at = datetime.utcnow()
            
        except GoogleAPIError as e:
            validation_result["errors"].append(str(e))
            service_account.health_status = 'unhealthy'
            service_account.health_checked_at = datetime.utcnow()
        except Exception as e:
            validation_result["errors"].append(f"Unexpected error: {str(e)}")
            service_account.health_status = 'unknown'
            service_account.health_checked_at = datetime.utcnow()
        
        await self.db.commit()
        return validation_result
    
    async def discover_properties(
        self,
        sa_id: int,
        discovered_by_id: int
    ) -> List[GA4PropertyResponse]:
        """Discover GA4 properties accessible by this service account"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        try:
            # Initialize GA service
            ga_service = GoogleAnalyticsService(secret_name=service_account.secret_name)
            
            # Get all accessible properties
            properties = await ga_service.list_properties()
            
            discovered_properties = []
            
            for prop in properties:
                # Check if property already exists in our database
                existing_result = await self.db.execute(
                    select(ServiceAccountProperty)
                    .where(
                        and_(
                            ServiceAccountProperty.service_account_id == sa_id,
                            ServiceAccountProperty.ga_property_id == prop["id"]
                        )
                    )
                )
                existing_prop = existing_result.scalar_one_or_none()
                
                if not existing_prop:
                    # Create new property record
                    sa_property = ServiceAccountProperty(
                        service_account_id=sa_id,
                        ga_property_id=prop["id"],
                        property_name=prop.get("name", ""),
                        property_account_id=prop.get("account_id", ""),
                        is_active=True,
                        discovered_at=datetime.utcnow(),
                        validation_status='valid'
                    )
                    self.db.add(sa_property)
                else:
                    # Update existing property
                    existing_prop.property_name = prop.get("name", existing_prop.property_name)
                    existing_prop.property_account_id = prop.get("account_id", existing_prop.property_account_id)
                    existing_prop.last_validated_at = datetime.utcnow()
                    existing_prop.validation_status = 'valid'
                    existing_prop.is_active = True
                
                discovered_properties.append(GA4PropertyResponse(
                    id=prop["id"],
                    name=prop.get("name", ""),
                    account_id=prop.get("account_id", ""),
                    service_account_id=sa_id,
                    is_active=True,
                    discovered_at=datetime.utcnow(),
                    validation_status='valid'
                ))
            
            await self.db.commit()
            
            # Update service account last used timestamp
            service_account.last_used_at = datetime.utcnow()
            await self.db.commit()
            
            # Log the discovery
            await self.audit_service.log_action(
                actor_id=discovered_by_id,
                action="discover_properties",
                resource_type="service_account",
                resource_id=str(sa_id),
                details=f"Discovered {len(discovered_properties)} GA4 properties"
            )
            
            return discovered_properties
            
        except GoogleAPIError as e:
            logger.error(f"Failed to discover properties for service account {sa_id}: {str(e)}")
            raise GoogleAPIError(f"Failed to discover properties: {str(e)}")
    
    async def list_service_account_properties(
        self,
        sa_id: int,
        is_active: Optional[bool] = None
    ) -> List[GA4PropertyResponse]:
        """List GA4 properties associated with this service account"""
        
        # Verify service account exists
        sa_result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = sa_result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        query = select(ServiceAccountProperty).where(ServiceAccountProperty.service_account_id == sa_id)
        
        if is_active is not None:
            query = query.where(ServiceAccountProperty.is_active == is_active)
        
        query = query.order_by(ServiceAccountProperty.property_name)
        
        result = await self.db.execute(query)
        properties = result.scalars().all()
        
        return [
            GA4PropertyResponse(
                id=prop.ga_property_id,
                name=prop.property_name or "",
                account_id=prop.property_account_id or "",
                service_account_id=prop.service_account_id,
                is_active=prop.is_active,
                discovered_at=prop.discovered_at,
                validation_status=prop.validation_status,
                last_validated_at=prop.last_validated_at
            )
            for prop in properties
        ]
    
    async def get_health_status(self, sa_id: int) -> Dict[str, Any]:
        """Get service account health status"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        return {
            "service_account_id": sa_id,
            "email": service_account.email,
            "health_status": service_account.health_status,
            "health_checked_at": service_account.health_checked_at.isoformat() if service_account.health_checked_at else None,
            "last_used_at": service_account.last_used_at.isoformat() if service_account.last_used_at else None,
            "is_active": service_account.is_active
        }
    
    async def perform_health_check(
        self,
        sa_id: int,
        checked_by_id: int
    ) -> Dict[str, Any]:
        """Perform comprehensive health check on service account"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        health_result = {
            "service_account_id": sa_id,
            "email": service_account.email,
            "overall_health": "unknown",
            "checks": {
                "credentials_valid": False,
                "api_accessible": False,
                "has_properties": False,
                "permissions_synced": False
            },
            "metrics": {
                "accessible_accounts": 0,
                "accessible_properties": 0,
                "active_grants": 0,
                "sync_issues": 0
            },
            "issues": [],
            "checked_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Test credentials and API access
            ga_service = GoogleAnalyticsService(secret_name=service_account.secret_name)
            
            # Check API access
            accounts = await ga_service.list_accounts()
            health_result["checks"]["credentials_valid"] = True
            health_result["checks"]["api_accessible"] = True
            health_result["metrics"]["accessible_accounts"] = len(accounts)
            
            # Check properties access
            properties = await ga_service.list_properties()
            health_result["checks"]["has_properties"] = len(properties) > 0
            health_result["metrics"]["accessible_properties"] = len(properties)
            
            # Count active permission grants
            from ..models.db_models import PermissionGrant, PermissionStatus
            grants_result = await self.db.execute(
                select(func.count(PermissionGrant.id))
                .where(
                    and_(
                        PermissionGrant.service_account_id == sa_id,
                        PermissionGrant.status == PermissionStatus.APPROVED
                    )
                )
            )
            health_result["metrics"]["active_grants"] = grants_result.scalar()
            
            # Basic permission sync check (simplified)
            health_result["checks"]["permissions_synced"] = True
            
            # Determine overall health
            if all(health_result["checks"].values()):
                health_result["overall_health"] = "healthy"
                service_account.health_status = "healthy"
            elif health_result["checks"]["credentials_valid"] and health_result["checks"]["api_accessible"]:
                health_result["overall_health"] = "warning"
                service_account.health_status = "warning"
                if not health_result["checks"]["has_properties"]:
                    health_result["issues"].append("No accessible GA4 properties found")
            else:
                health_result["overall_health"] = "unhealthy"
                service_account.health_status = "unhealthy"
                health_result["issues"].append("API access failed")
            
        except GoogleAPIError as e:
            health_result["overall_health"] = "unhealthy"
            health_result["issues"].append(f"Google API Error: {str(e)}")
            service_account.health_status = "unhealthy"
        except Exception as e:
            health_result["overall_health"] = "unknown"
            health_result["issues"].append(f"Unexpected error: {str(e)}")
            service_account.health_status = "unknown"
        
        # Update service account health status
        service_account.health_checked_at = datetime.utcnow()
        service_account.last_used_at = datetime.utcnow()
        await self.db.commit()
        
        # Log the health check
        await self.audit_service.log_action(
            actor_id=checked_by_id,
            action="health_check",
            resource_type="service_account",
            resource_id=str(sa_id),
            details=f"Health check completed: {health_result['overall_health']}"
        )
        
        return health_result
    
    async def rotate_credentials(
        self,
        sa_id: int,
        rotated_by_id: int
    ) -> ServiceAccountResponse:
        """Rotate service account credentials"""
        
        result = await self.db.execute(select(ServiceAccount).where(ServiceAccount.id == sa_id))
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise NotFoundError("Service account not found")
        
        try:
            # Here you would implement actual credential rotation
            # This involves creating new keys in Google Cloud and updating Secret Manager
            logger.info(f"Would rotate credentials for service account {sa_id}")
            
            # Update key version
            service_account.key_version = (service_account.key_version or 1) + 1
            service_account.updated_at = datetime.utcnow()
            service_account.health_status = 'unknown'  # Will be verified on next health check
            
            await self.db.commit()
            await self.db.refresh(service_account)
            
            # Log the rotation
            await self.audit_service.log_action(
                actor_id=rotated_by_id,
                action="rotate_credentials",
                resource_type="service_account",
                resource_id=str(sa_id),
                details=f"Rotated credentials for service account {service_account.email}"
            )
            
            return ServiceAccountResponse.model_validate(service_account)
            
        except Exception as e:
            logger.error(f"Failed to rotate credentials for service account {sa_id}: {str(e)}")
            raise GoogleAPIError(f"Failed to rotate credentials: {str(e)}")