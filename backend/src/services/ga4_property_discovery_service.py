"""
GA4 Property Discovery Service - discovers and synchronizes GA4 properties for service accounts
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update, delete
from sqlalchemy.orm import selectinload

from ..models.db_models import (
    ServiceAccount, ServiceAccountProperty, PropertyAccessBinding,
    Client, User, PermissionGrant
)
from ..models.schemas import (
    ServiceAccountPropertyResponse, PropertyAccessBindingResponse,
    ValidationResultResponse
)
from ..core.exceptions import (
    ValidationError, BusinessRuleViolationError, ExternalApiError,
    ResourceNotFoundError
)
from .google_api_service import GoogleAnalyticsService
from .audit_service import AuditService


class GA4PropertyDiscoveryService:
    """Service for discovering and managing GA4 properties through service accounts"""
    
    def __init__(
        self, 
        db: AsyncSession,
        google_api_service: GoogleAnalyticsService,
        audit_service: AuditService
    ):
        self.db = db
        self.google_api_service = google_api_service
        self.audit_service = audit_service
    
    async def discover_properties_for_service_account(
        self, 
        service_account_id: int,
        force_refresh: bool = False
    ) -> List[ServiceAccountPropertyResponse]:
        """
        Discover GA4 properties accessible by a service account
        
        This method:
        1. Validates the service account credentials
        2. Calls GA4 Admin API to discover accessible accounts and properties
        3. Updates the database with discovered properties
        4. Returns the list of discovered properties
        """
        
        # Get the service account
        query = (
            select(ServiceAccount)
            .options(selectinload(ServiceAccount.client))
            .where(ServiceAccount.id == service_account_id)
        )
        result = await self.db.execute(query)
        service_account = result.scalar_one_or_none()
        
        if not service_account:
            raise ResourceNotFoundError(f"Service account {service_account_id} not found")
        
        if not service_account.is_active:
            raise ValidationError(f"Service account {service_account_id} is inactive")
        
        # Check if we need to refresh (force refresh or not discovered recently)
        if not force_refresh:
            # Check if we have recent discoveries (within last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_count_query = (
                select(func.count(ServiceAccountProperty.id))
                .where(
                    and_(
                        ServiceAccountProperty.service_account_id == service_account_id,
                        ServiceAccountProperty.discovered_at >= recent_cutoff
                    )
                )
            )
            result = await self.db.execute(recent_count_query)
            recent_count = result.scalar()
            
            if recent_count > 0:
                # Return existing properties
                return await self._get_service_account_properties(service_account_id)
        
        try:
            # Discover properties through Google API
            discovery_result = await self.google_api_service.discover_ga4_properties(
                service_account
            )
            
            # Update service account health status
            service_account.health_status = 'healthy' if discovery_result.get('success') else 'unhealthy'
            service_account.health_checked_at = datetime.utcnow()
            service_account.last_used_at = datetime.utcnow()
            
            if not discovery_result.get('success'):
                await self.db.commit()
                raise ExternalApiError(f"Failed to discover properties: {discovery_result.get('error')}")
            
            # Process discovered properties
            discovered_properties = discovery_result.get('properties', [])
            await self._update_service_account_properties(service_account_id, discovered_properties)
            
            await self.db.commit()
            
            # Log the discovery
            await self.audit_service.log_action(
                actor_id=None,  # System action
                action="discover_ga4_properties",
                resource_type="service_account",
                resource_id=str(service_account_id),
                details={
                    "discovered_count": len(discovered_properties),
                    "force_refresh": force_refresh,
                    "client_id": service_account.client_id
                }
            )
            
            return await self._get_service_account_properties(service_account_id)
            
        except Exception as e:
            # Update service account health status on error
            service_account.health_status = 'unhealthy'
            service_account.health_checked_at = datetime.utcnow()
            await self.db.commit()
            
            if isinstance(e, (ValidationError, BusinessRuleViolationError, ExternalApiError)):
                raise
            else:
                raise ExternalApiError(f"Unexpected error during property discovery: {str(e)}")
    
    async def _update_service_account_properties(
        self, 
        service_account_id: int, 
        discovered_properties: List[Dict[str, Any]]
    ) -> None:
        """Update the database with discovered properties"""
        
        discovered_property_ids = set()
        
        for prop_data in discovered_properties:
            property_id = prop_data.get('property_id')
            if not property_id:
                continue
                
            discovered_property_ids.add(property_id)
            
            # Check if property already exists
            existing_query = (
                select(ServiceAccountProperty)
                .where(
                    and_(
                        ServiceAccountProperty.service_account_id == service_account_id,
                        ServiceAccountProperty.ga_property_id == property_id
                    )
                )
            )
            result = await self.db.execute(existing_query)
            existing_property = result.scalar_one_or_none()
            
            if existing_property:
                # Update existing property
                existing_property.property_name = prop_data.get('display_name', existing_property.property_name)
                existing_property.property_account_id = prop_data.get('account_id', existing_property.property_account_id)
                existing_property.is_active = True
                existing_property.discovered_at = datetime.utcnow()
                existing_property.validation_status = 'valid'
                existing_property.last_validated_at = datetime.utcnow()
                existing_property.updated_at = datetime.utcnow()
            else:
                # Create new property
                new_property = ServiceAccountProperty(
                    service_account_id=service_account_id,
                    ga_property_id=property_id,
                    property_name=prop_data.get('display_name'),
                    property_account_id=prop_data.get('account_id'),
                    is_active=True,
                    discovered_at=datetime.utcnow(),
                    last_validated_at=datetime.utcnow(),
                    validation_status='valid'
                )
                self.db.add(new_property)
        
        # Mark properties not found in discovery as inactive
        if discovered_property_ids:
            inactive_update = (
                update(ServiceAccountProperty)
                .where(
                    and_(
                        ServiceAccountProperty.service_account_id == service_account_id,
                        ServiceAccountProperty.ga_property_id.notin_(discovered_property_ids),
                        ServiceAccountProperty.is_active == True
                    )
                )
                .values(
                    is_active=False,
                    validation_status='invalid',
                    last_validated_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.execute(inactive_update)
    
    async def _get_service_account_properties(
        self, 
        service_account_id: int
    ) -> List[ServiceAccountPropertyResponse]:
        """Get all properties for a service account"""
        
        query = (
            select(ServiceAccountProperty)
            .where(ServiceAccountProperty.service_account_id == service_account_id)
            .order_by(ServiceAccountProperty.property_name.asc().nullslast())
        )
        
        result = await self.db.execute(query)
        properties = result.scalars().all()
        
        return [
            ServiceAccountPropertyResponse(
                id=prop.id,
                service_account_id=prop.service_account_id,
                ga_property_id=prop.ga_property_id,
                property_name=prop.property_name,
                property_account_id=prop.property_account_id,
                is_active=prop.is_active,
                discovered_at=prop.discovered_at,
                last_validated_at=prop.last_validated_at,
                validation_status=prop.validation_status,
                created_at=prop.created_at,
                updated_at=prop.updated_at
            )
            for prop in properties
        ]
    
    async def synchronize_property_permissions(
        self, 
        service_account_id: int,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronize permissions between GA4 and internal database
        
        This method:
        1. Gets current GA4 permissions for properties
        2. Compares with internal permission grants
        3. Identifies discrepancies
        4. Updates the PropertyAccessBinding cache
        5. Returns synchronization report
        """
        
        # Get service account
        service_account = await self.db.get(ServiceAccount, service_account_id)
        if not service_account:
            raise ResourceNotFoundError(f"Service account {service_account_id} not found")
        
        # Get properties to synchronize
        properties_query = (
            select(ServiceAccountProperty)
            .where(
                and_(
                    ServiceAccountProperty.service_account_id == service_account_id,
                    ServiceAccountProperty.is_active == True
                )
            )
        )
        
        if property_id:
            properties_query = properties_query.where(
                ServiceAccountProperty.ga_property_id == property_id
            )
        
        result = await self.db.execute(properties_query)
        properties = result.scalars().all()
        
        sync_report = {
            "service_account_id": service_account_id,
            "service_account_email": service_account.email,
            "synchronized_at": datetime.utcnow().isoformat(),
            "properties": [],
            "total_properties": len(properties),
            "total_bindings_synced": 0,
            "errors": []
        }
        
        for prop in properties:
            try:
                property_sync = await self._sync_single_property_permissions(
                    service_account, prop
                )
                sync_report["properties"].append(property_sync)
                sync_report["total_bindings_synced"] += property_sync.get("bindings_count", 0)
                
            except Exception as e:
                error_msg = f"Failed to sync property {prop.ga_property_id}: {str(e)}"
                sync_report["errors"].append(error_msg)
                sync_report["properties"].append({
                    "property_id": prop.ga_property_id,
                    "property_name": prop.property_name,
                    "status": "error",
                    "error": error_msg,
                    "bindings_count": 0
                })
        
        await self.db.commit()
        
        # Log synchronization
        await self.audit_service.log_action(
            actor_id=None,  # System action
            action="synchronize_property_permissions",
            resource_type="service_account",
            resource_id=str(service_account_id),
            details={
                "properties_count": sync_report["total_properties"],
                "bindings_synced": sync_report["total_bindings_synced"],
                "errors_count": len(sync_report["errors"]),
                "specific_property": property_id
            }
        )
        
        return sync_report
    
    async def _sync_single_property_permissions(
        self, 
        service_account: ServiceAccount,
        property_obj: ServiceAccountProperty
    ) -> Dict[str, Any]:
        """Synchronize permissions for a single property"""
        
        property_sync = {
            "property_id": property_obj.ga_property_id,
            "property_name": property_obj.property_name,
            "status": "success",
            "bindings_count": 0,
            "discrepancies": []
        }
        
        try:
            # Get current GA4 permissions
            ga4_permissions = await self.google_api_service.get_property_permissions(
                service_account, property_obj.ga_property_id
            )
            
            if not ga4_permissions.get('success'):
                property_sync["status"] = "error"
                property_sync["error"] = ga4_permissions.get('error', 'Unknown error')
                return property_sync
            
            bindings = ga4_permissions.get('bindings', [])
            property_sync["bindings_count"] = len(bindings)
            
            # Update PropertyAccessBinding cache
            await self._update_property_access_bindings(
                service_account.id, property_obj.ga_property_id, bindings
            )
            
            # Get internal permission grants for comparison
            grants_query = (
                select(PermissionGrant)
                .where(
                    and_(
                        PermissionGrant.service_account_id == service_account.id,
                        PermissionGrant.ga_property_id == property_obj.ga_property_id,
                        PermissionGrant.status == 'approved'
                    )
                )
            )
            result = await self.db.execute(grants_query)
            internal_grants = result.scalars().all()
            
            # Compare and identify discrepancies
            discrepancies = await self._identify_permission_discrepancies(
                bindings, internal_grants
            )
            property_sync["discrepancies"] = discrepancies
            
        except Exception as e:
            property_sync["status"] = "error"
            property_sync["error"] = str(e)
        
        return property_sync
    
    async def _update_property_access_bindings(
        self, 
        service_account_id: int,
        property_id: str,
        bindings: List[Dict[str, Any]]
    ) -> None:
        """Update the PropertyAccessBinding cache with current GA4 bindings"""
        
        # Clear existing bindings for this property
        delete_query = delete(PropertyAccessBinding).where(
            and_(
                PropertyAccessBinding.service_account_id == service_account_id,
                PropertyAccessBinding.ga_property_id == property_id
            )
        )
        await self.db.execute(delete_query)
        
        # Add current bindings
        for binding in bindings:
            user_email = binding.get('user_email', '')
            roles = binding.get('roles', [])
            binding_name = binding.get('binding_name', '')
            
            if user_email and roles:
                access_binding = PropertyAccessBinding(
                    service_account_id=service_account_id,
                    ga_property_id=property_id,
                    user_email=user_email,
                    roles=str(roles),  # Store as JSON string
                    binding_name=binding_name,
                    is_active=True,
                    synchronized_at=datetime.utcnow()
                )
                self.db.add(access_binding)
    
    async def _identify_permission_discrepancies(
        self, 
        ga4_bindings: List[Dict[str, Any]],
        internal_grants: List[PermissionGrant]
    ) -> List[Dict[str, Any]]:
        """Identify discrepancies between GA4 and internal permissions"""
        
        discrepancies = []
        
        # Create lookup maps
        ga4_permissions = {}
        for binding in ga4_bindings:
            email = binding.get('user_email', '').lower()
            roles = binding.get('roles', [])
            ga4_permissions[email] = roles
        
        internal_permissions = {}
        for grant in internal_grants:
            email = grant.target_email.lower()
            internal_permissions[email] = grant.permission_level.value
        
        # Find permissions in GA4 but not in internal system
        for email, roles in ga4_permissions.items():
            if email not in internal_permissions:
                discrepancies.append({
                    "type": "ga4_only",
                    "user_email": email,
                    "ga4_roles": roles,
                    "internal_permission": None,
                    "description": f"User {email} has GA4 access but no internal grant record"
                })
        
        # Find permissions in internal system but not in GA4
        for email, permission in internal_permissions.items():
            if email not in ga4_permissions:
                discrepancies.append({
                    "type": "internal_only",
                    "user_email": email,
                    "ga4_roles": None,
                    "internal_permission": permission,
                    "description": f"User {email} has internal grant but no GA4 access"
                })
            else:
                # Check for role mismatches
                ga4_roles = ga4_permissions[email]
                expected_role = self._permission_level_to_ga4_role(permission)
                if expected_role not in ga4_roles:
                    discrepancies.append({
                        "type": "role_mismatch",
                        "user_email": email,
                        "ga4_roles": ga4_roles,
                        "internal_permission": permission,
                        "expected_ga4_role": expected_role,
                        "description": f"User {email} has mismatched roles between GA4 and internal system"
                    })
        
        return discrepancies
    
    def _permission_level_to_ga4_role(self, permission_level: str) -> str:
        """Convert internal permission level to GA4 role"""
        mapping = {
            "viewer": "predefinedRoles/ga4:read",
            "analyst": "predefinedRoles/ga4:read",
            "marketer": "predefinedRoles/ga4:standard",
            "editor": "predefinedRoles/ga4:edit",
            "administrator": "predefinedRoles/ga4:admin"
        }
        return mapping.get(permission_level.lower(), "predefinedRoles/ga4:read")
    
    async def validate_service_account_access(
        self, 
        service_account_id: int
    ) -> ValidationResultResponse:
        """
        Validate that a service account has proper GA4 access
        
        This performs a comprehensive validation of the service account:
        1. Checks credentials validity
        2. Tests GA4 API access
        3. Discovers accessible accounts and properties
        4. Updates health status
        """
        
        # Get service account
        service_account = await self.db.get(ServiceAccount, service_account_id)
        if not service_account:
            raise ResourceNotFoundError(f"Service account {service_account_id} not found")
        
        validation_result = ValidationResultResponse(
            service_account_id=service_account_id,
            email=service_account.email,
            is_valid=False,
            has_ga4_access=False,
            accessible_accounts=[],
            accessible_properties=[],
            errors=[],
            validated_at=datetime.utcnow().isoformat()
        )
        
        try:
            # Test GA4 API access
            api_test = await self.google_api_service.test_service_account_access(service_account)
            
            validation_result.is_valid = api_test.get('credentials_valid', False)
            validation_result.has_ga4_access = api_test.get('ga4_access', False)
            validation_result.accessible_accounts = api_test.get('accounts', [])
            validation_result.accessible_properties = api_test.get('properties', [])
            validation_result.errors = api_test.get('errors', [])
            
            # Update service account health
            if validation_result.is_valid and validation_result.has_ga4_access:
                service_account.health_status = 'healthy'
            elif validation_result.is_valid:
                service_account.health_status = 'warning'  # Valid credentials but no GA4 access
            else:
                service_account.health_status = 'unhealthy'
            
            service_account.health_checked_at = datetime.utcnow()
            service_account.last_used_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log validation
            await self.audit_service.log_action(
                actor_id=None,  # System action
                action="validate_service_account_access",
                resource_type="service_account",
                resource_id=str(service_account_id),
                details={
                    "is_valid": validation_result.is_valid,
                    "has_ga4_access": validation_result.has_ga4_access,
                    "accounts_count": len(validation_result.accessible_accounts),
                    "properties_count": len(validation_result.accessible_properties),
                    "errors_count": len(validation_result.errors)
                }
            )
            
        except Exception as e:
            validation_result.errors.append(f"Validation failed: {str(e)}")
            service_account.health_status = 'unhealthy'
            service_account.health_checked_at = datetime.utcnow()
            await self.db.commit()
        
        return validation_result
    
    async def get_client_property_summary(self, client_id: int) -> Dict[str, Any]:
        """Get a summary of properties available through a client's service accounts"""
        
        # Get client with service accounts and properties
        query = (
            select(Client)
            .options(
                selectinload(Client.service_accounts).selectinload(ServiceAccount.service_account_properties)
            )
            .where(Client.id == client_id)
        )
        
        result = await self.db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise ResourceNotFoundError(f"Client {client_id} not found")
        
        summary = {
            "client_id": client_id,
            "client_name": client.name,
            "service_accounts_count": 0,
            "total_properties": 0,
            "active_properties": 0,
            "service_accounts": [],
            "health_summary": {
                "healthy": 0,
                "warning": 0,
                "unhealthy": 0,
                "unknown": 0
            }
        }
        
        for sa in client.service_accounts:
            if not sa.is_active:
                continue
                
            sa_properties = [p for p in sa.service_account_properties if p.is_active]
            
            summary["service_accounts_count"] += 1
            summary["total_properties"] += len(sa.service_account_properties)
            summary["active_properties"] += len(sa_properties)
            summary["health_summary"][sa.health_status] += 1
            
            summary["service_accounts"].append({
                "id": sa.id,
                "email": sa.email,
                "display_name": sa.display_name,
                "health_status": sa.health_status,
                "properties_count": len(sa_properties),
                "last_discovery": max([p.discovered_at for p in sa_properties]) if sa_properties else None
            })
        
        return summary