"""
Permission Request Service - handles GA4 permission request workflow
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload

from ..models.db_models import (
    PermissionRequest, PermissionGrant, User, Client, ServiceAccount, 
    ServiceAccountProperty, ClientAssignment, UserRole, PermissionLevel,
    PermissionRequestStatus, PermissionStatus, ClientAssignmentStatus
)
from ..models.schemas import (
    PermissionRequestCreate, PermissionRequestResponse, 
    ClientPropertiesResponse, ServiceAccountWithPropertiesResponse,
    AutoApprovalRuleResponse
)
from ..core.exceptions import (
    ValidationError, BusinessRuleViolationError, DuplicateResourceError,
    UnauthorizedError, ResourceNotFoundError
)
from .client_assignment_service import ClientAssignmentService
from .google_api_service import GoogleAnalyticsService
from .audit_service import AuditService


class PermissionRequestService:
    """Service for managing GA4 permission requests"""
    
    def __init__(
        self, 
        db: AsyncSession,
        client_assignment_service: ClientAssignmentService,
        google_api_service: GoogleAnalyticsService,
        audit_service: AuditService
    ):
        self.db = db
        self.client_assignment_service = client_assignment_service
        self.google_api_service = google_api_service
        self.audit_service = audit_service
    
    async def get_client_available_properties(
        self, 
        user_id: int, 
        client_id: int
    ) -> ClientPropertiesResponse:
        """
        Get GA4 properties available for a client that the user is assigned to
        
        Business Logic:
        1. Verify user is assigned to the client
        2. Get all service accounts for the client
        3. Get all properties for each service account
        4. Return structured response
        """
        
        # 1. Verify user assignment to client
        is_assigned = await self.client_assignment_service.is_user_assigned_to_client(
            user_id, client_id
        )
        if not is_assigned:
            raise UnauthorizedError(f"User {user_id} is not assigned to client {client_id}")
        
        # 2. Get client with service accounts and properties
        query = (
            select(Client)
            .options(
                selectinload(Client.service_accounts).selectinload(ServiceAccount.service_account_properties)
            )
            .where(
                and_(
                    Client.id == client_id,
                    Client.is_active == True
                )
            )
        )
        
        result = await self.db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise ResourceNotFoundError(f"Client {client_id} not found or inactive")
        
        # 3. Build response with service accounts and properties
        service_accounts_data = []
        total_properties = 0
        
        for sa in client.service_accounts:
            if not sa.is_active:
                continue
                
            properties_data = []
            for prop in sa.service_account_properties:
                if prop.is_active:
                    properties_data.append({
                        "id": prop.id,
                        "service_account_id": prop.service_account_id,
                        "ga_property_id": prop.ga_property_id,
                        "property_name": prop.property_name,
                        "property_account_id": prop.property_account_id,
                        "is_active": prop.is_active,
                        "discovered_at": prop.discovered_at,
                        "last_validated_at": prop.last_validated_at,
                        "validation_status": prop.validation_status,
                        "created_at": prop.created_at,
                        "updated_at": prop.updated_at
                    })
            
            if properties_data:  # Only include SAs with active properties
                service_accounts_data.append(ServiceAccountWithPropertiesResponse(
                    id=sa.id,
                    email=sa.email,
                    display_name=sa.display_name,
                    is_active=sa.is_active,
                    health_status=sa.health_status,
                    properties=properties_data
                ))
                total_properties += len(properties_data)
        
        return ClientPropertiesResponse(
            client_id=client.id,
            client_name=client.name,
            service_accounts=service_accounts_data,
            total_properties=total_properties
        )
    
    async def submit_permission_request(
        self, 
        user_id: int, 
        request_data: PermissionRequestCreate
    ) -> PermissionRequestResponse:
        """
        Submit a new permission request
        
        Business Logic:
        1. Validate user assignment to client
        2. Validate property exists and is accessible
        3. Check for duplicate pending requests
        4. Evaluate auto-approval rules
        5. Create permission request
        6. If auto-approved, immediately create permission grant
        """
        
        # 1. Validate user assignment to client
        is_assigned = await self.client_assignment_service.is_user_assigned_to_client(
            user_id, request_data.client_id
        )
        if not is_assigned:
            raise UnauthorizedError(f"User {user_id} is not assigned to client {request_data.client_id}")
        
        # 2. Get user for auto-approval evaluation
        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        # 3. Validate property exists and is accessible through client's service accounts
        property_query = (
            select(ServiceAccountProperty)
            .join(ServiceAccount)
            .where(
                and_(
                    ServiceAccount.client_id == request_data.client_id,
                    ServiceAccount.is_active == True,
                    ServiceAccountProperty.ga_property_id == request_data.ga_property_id,
                    ServiceAccountProperty.is_active == True
                )
            )
        )
        
        result = await self.db.execute(property_query)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise ValidationError(
                f"GA4 Property {request_data.ga_property_id} not found or not accessible through client {request_data.client_id}"
            )
        
        # 4. Check for duplicate pending requests
        duplicate_query = (
            select(PermissionRequest)
            .where(
                and_(
                    PermissionRequest.user_id == user_id,
                    PermissionRequest.ga_property_id == request_data.ga_property_id,
                    PermissionRequest.target_email == request_data.target_email,
                    PermissionRequest.status.in_([
                        PermissionRequestStatus.PENDING,
                        PermissionRequestStatus.AUTO_APPROVED
                    ])
                )
            )
        )
        
        result = await self.db.execute(duplicate_query)
        duplicate = result.scalar_one_or_none()
        
        if duplicate:
            raise DuplicateResourceError(
                f"Pending permission request already exists for property {request_data.ga_property_id} and email {request_data.target_email}"
            )
        
        # 5. Evaluate auto-approval rules
        auto_approval = await self.evaluate_auto_approval(
            user.role, request_data.permission_level, request_data.client_id
        )
        
        # 6. Create permission request
        permission_request = PermissionRequest(
            user_id=user_id,
            client_id=request_data.client_id,
            ga_property_id=request_data.ga_property_id,
            target_email=request_data.target_email,
            permission_level=request_data.permission_level,
            business_justification=request_data.business_justification,
            requested_duration_days=request_data.requested_duration_days,
            auto_approved=auto_approval.auto_approved,
            requires_approval_from_role=auto_approval.requires_approval_from_role,
            status=PermissionRequestStatus.AUTO_APPROVED if auto_approval.auto_approved else PermissionRequestStatus.PENDING
        )
        
        self.db.add(permission_request)
        await self.db.flush()  # Get the ID
        
        # 7. If auto-approved, immediately process the request
        if auto_approval.auto_approved:
            await self._process_auto_approved_request(permission_request, property_obj.service_account_id)
        
        await self.db.commit()
        
        # 8. Log the action
        await self.audit_service.log_action(
            actor_id=user_id,
            action="submit_permission_request",
            resource_type="permission_request",
            resource_id=str(permission_request.id),
            details={
                "client_id": request_data.client_id,
                "ga_property_id": request_data.ga_property_id,
                "permission_level": request_data.permission_level,
                "auto_approved": auto_approval.auto_approved
            }
        )
        
        # 9. Return response
        return await self._build_permission_request_response(permission_request)
    
    async def evaluate_auto_approval(
        self, 
        user_role: UserRole, 
        permission_level: PermissionLevel,
        client_id: int
    ) -> AutoApprovalRuleResponse:
        """
        Evaluate if a permission request should be auto-approved
        
        Auto-approval Rules:
        - Viewer/Analyst: Auto-approved for Requesters and above
        - Marketer: Requires Admin approval
        - Editor: Requires Admin approval  
        - Administrator: Requires Super Admin approval
        """
        
        auto_approved = False
        requires_approval_from_role = None
        reason = ""
        
        if permission_level in [PermissionLevel.VIEWER, PermissionLevel.ANALYST]:
            if user_role in [UserRole.REQUESTER, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                auto_approved = True
                reason = f"{permission_level.value} permissions are auto-approved for {user_role.value} role"
            else:
                requires_approval_from_role = UserRole.ADMIN
                reason = f"{permission_level.value} permissions require Admin approval for {user_role.value} role"
        
        elif permission_level in [PermissionLevel.MARKETER, PermissionLevel.EDITOR]:
            if user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                auto_approved = True
                reason = f"{permission_level.value} permissions are auto-approved for {user_role.value} role"
            else:
                requires_approval_from_role = UserRole.ADMIN
                reason = f"{permission_level.value} permissions require Admin approval"
        
        elif permission_level == PermissionLevel.ADMINISTRATOR:
            requires_approval_from_role = UserRole.SUPER_ADMIN
            reason = f"{permission_level.value} permissions always require Super Admin approval"
        
        return AutoApprovalRuleResponse(
            permission_level=permission_level,
            user_role=user_role,
            auto_approved=auto_approved,
            requires_approval_from_role=requires_approval_from_role,
            reason=reason
        )
    
    async def _process_auto_approved_request(
        self, 
        permission_request: PermissionRequest,
        service_account_id: int
    ) -> None:
        """Process an auto-approved permission request by creating a permission grant"""
        
        # Calculate expiration date
        expires_at = None
        if permission_request.requested_duration_days:
            expires_at = datetime.utcnow() + timedelta(days=permission_request.requested_duration_days)
        elif permission_request.permission_level in [PermissionLevel.VIEWER, PermissionLevel.ANALYST]:
            # Default 30 days for viewer/analyst
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Create permission grant
        permission_grant = PermissionGrant(
            user_id=permission_request.user_id,
            client_id=permission_request.client_id,
            service_account_id=service_account_id,
            ga_property_id=permission_request.ga_property_id,
            target_email=permission_request.target_email,
            permission_level=permission_request.permission_level,
            status=PermissionStatus.APPROVED,
            expires_at=expires_at,
            approved_at=datetime.utcnow(),
            approved_by_id=None,  # Auto-approved
            reason=permission_request.business_justification,
            sync_status='pending'
        )
        
        self.db.add(permission_grant)
        await self.db.flush()
        
        # Link the grant to the request
        permission_request.permission_grant_id = permission_grant.id
        permission_request.processed_at = datetime.utcnow()
        
        # TODO: Queue GA4 API call to actually grant the permission
        # await self.google_api_service.grant_property_permission(...)
    
    async def approve_permission_request(
        self, 
        request_id: int, 
        approver_id: int,
        processing_notes: Optional[str] = None
    ) -> PermissionRequestResponse:
        """Approve a pending permission request"""
        
        # Get the request
        query = (
            select(PermissionRequest)
            .options(selectinload(PermissionRequest.user))
            .where(PermissionRequest.id == request_id)
        )
        result = await self.db.execute(query)
        permission_request = result.scalar_one_or_none()
        
        if not permission_request:
            raise ResourceNotFoundError(f"Permission request {request_id} not found")
        
        if permission_request.status != PermissionRequestStatus.PENDING:
            raise BusinessRuleViolationError(f"Permission request {request_id} is not in pending status")
        
        # Get approver
        approver = await self.db.get(User, approver_id)
        if not approver:
            raise ResourceNotFoundError(f"Approver {approver_id} not found")
        
        # Validate approver has sufficient role
        if permission_request.requires_approval_from_role:
            if not self._has_sufficient_role(approver.role, permission_request.requires_approval_from_role):
                raise UnauthorizedError(
                    f"Approver role {approver.role.value} insufficient. Required: {permission_request.requires_approval_from_role.value}"
                )
        
        # Find the service account for this property
        property_query = (
            select(ServiceAccountProperty)
            .join(ServiceAccount)
            .where(
                and_(
                    ServiceAccount.client_id == permission_request.client_id,
                    ServiceAccount.is_active == True,
                    ServiceAccountProperty.ga_property_id == permission_request.ga_property_id,
                    ServiceAccountProperty.is_active == True
                )
            )
        )
        
        result = await self.db.execute(property_query)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise ValidationError(f"Service account for property {permission_request.ga_property_id} not found")
        
        # Update request status
        permission_request.status = PermissionRequestStatus.APPROVED
        permission_request.processed_at = datetime.utcnow()
        permission_request.processed_by_id = approver_id
        permission_request.processing_notes = processing_notes
        
        # Process the approved request
        await self._process_auto_approved_request(permission_request, property_obj.service_account_id)
        
        await self.db.commit()
        
        # Log the action
        await self.audit_service.log_action(
            actor_id=approver_id,
            action="approve_permission_request",
            resource_type="permission_request",
            resource_id=str(request_id),
            details={
                "user_id": permission_request.user_id,
                "ga_property_id": permission_request.ga_property_id,
                "permission_level": permission_request.permission_level.value,
                "processing_notes": processing_notes
            }
        )
        
        return await self._build_permission_request_response(permission_request)
    
    async def reject_permission_request(
        self, 
        request_id: int, 
        approver_id: int,
        processing_notes: str
    ) -> PermissionRequestResponse:
        """Reject a pending permission request"""
        
        # Get the request
        permission_request = await self.db.get(PermissionRequest, request_id)
        if not permission_request:
            raise ResourceNotFoundError(f"Permission request {request_id} not found")
        
        if permission_request.status != PermissionRequestStatus.PENDING:
            raise BusinessRuleViolationError(f"Permission request {request_id} is not in pending status")
        
        # Update request status
        permission_request.status = PermissionRequestStatus.REJECTED
        permission_request.processed_at = datetime.utcnow()
        permission_request.processed_by_id = approver_id
        permission_request.processing_notes = processing_notes
        
        await self.db.commit()
        
        # Log the action
        await self.audit_service.log_action(
            actor_id=approver_id,
            action="reject_permission_request",
            resource_type="permission_request",
            resource_id=str(request_id),
            details={
                "user_id": permission_request.user_id,
                "ga_property_id": permission_request.ga_property_id,
                "permission_level": permission_request.permission_level.value,
                "processing_notes": processing_notes
            }
        )
        
        return await self._build_permission_request_response(permission_request)
    
    async def get_user_permission_requests(
        self, 
        user_id: int,
        status: Optional[PermissionRequestStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PermissionRequestResponse]:
        """Get permission requests for a user"""
        
        query = (
            select(PermissionRequest)
            .options(
                selectinload(PermissionRequest.user),
                selectinload(PermissionRequest.client),
                selectinload(PermissionRequest.processed_by)
            )
            .where(PermissionRequest.user_id == user_id)
        )
        
        if status:
            query = query.where(PermissionRequest.status == status)
        
        query = query.order_by(desc(PermissionRequest.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return [await self._build_permission_request_response(req) for req in requests]
    
    async def get_pending_requests_for_approval(
        self, 
        approver_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[PermissionRequestResponse]:
        """Get pending permission requests that the approver can approve"""
        
        approver = await self.db.get(User, approver_id)
        if not approver:
            raise ResourceNotFoundError(f"Approver {approver_id} not found")
        
        # Build query based on approver role
        query = (
            select(PermissionRequest)
            .options(
                selectinload(PermissionRequest.user),
                selectinload(PermissionRequest.client),
                selectinload(PermissionRequest.processed_by)
            )
            .where(PermissionRequest.status == PermissionRequestStatus.PENDING)
        )
        
        # Filter by what this approver can approve
        if approver.role == UserRole.ADMIN:
            query = query.where(
                PermissionRequest.requires_approval_from_role.in_([
                    UserRole.ADMIN, 
                    None  # Auto-approved requests that somehow became pending
                ])
            )
        elif approver.role == UserRole.SUPER_ADMIN:
            # Super Admin can approve everything
            pass
        else:
            # Other roles cannot approve anything
            query = query.where(False)  # Return empty result
        
        query = query.order_by(desc(PermissionRequest.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return [await self._build_permission_request_response(req) for req in requests]
    
    def _has_sufficient_role(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role is sufficient for the required role"""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.REQUESTER: 2, 
            UserRole.ADMIN: 3,
            UserRole.SUPER_ADMIN: 4
        }
        
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
    
    async def _build_permission_request_response(
        self, 
        permission_request: PermissionRequest
    ) -> PermissionRequestResponse:
        """Build a complete permission request response"""
        
        # Load relationships if not already loaded
        if not hasattr(permission_request, 'user') or permission_request.user is None:
            await self.db.refresh(permission_request, ['user', 'client', 'processed_by'])
        
        return PermissionRequestResponse(
            id=permission_request.id,
            user_id=permission_request.user_id,
            client_id=permission_request.client_id,
            ga_property_id=permission_request.ga_property_id,
            target_email=permission_request.target_email,
            permission_level=permission_request.permission_level,
            status=permission_request.status,
            business_justification=permission_request.business_justification,
            requested_duration_days=permission_request.requested_duration_days,
            auto_approved=permission_request.auto_approved,
            requires_approval_from_role=permission_request.requires_approval_from_role,
            processed_at=permission_request.processed_at,
            processed_by_id=permission_request.processed_by_id,
            processing_notes=permission_request.processing_notes,
            permission_grant_id=permission_request.permission_grant_id,
            created_at=permission_request.created_at,
            updated_at=permission_request.updated_at,
            user={
                "id": permission_request.user.id,
                "email": permission_request.user.email,
                "name": permission_request.user.name,
                "role": permission_request.user.role,
                "status": permission_request.user.status
            } if permission_request.user else None,
            client={
                "id": permission_request.client.id,
                "name": permission_request.client.name,
                "is_active": permission_request.client.is_active
            } if permission_request.client else None,
            processed_by={
                "id": permission_request.processed_by.id,
                "email": permission_request.processed_by.email,
                "name": permission_request.processed_by.name,
                "role": permission_request.processed_by.role
            } if permission_request.processed_by else None
        )