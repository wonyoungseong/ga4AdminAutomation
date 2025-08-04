"""
Permission Request API endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_async_db
from ...core.auth_dependencies import get_current_user, require_role
from ...models.db_models import User, UserRole, PermissionRequestStatus
from ...models.schemas import (
    PermissionRequestCreate, PermissionRequestResponse, PermissionRequestUpdate,
    ClientPropertiesResponse, AutoApprovalRuleResponse, MessageResponse,
    PaginatedResponse
)
from ...services.permission_request_service import PermissionRequestService
from ...services.client_assignment_service import ClientAssignmentService
from ...services.google_api_service import GoogleApiService
from ...services.audit_service import AuditService
from ...core.exceptions import (
    ValidationError, BusinessRuleViolationError, DuplicateResourceError,
    UnauthorizedError, ResourceNotFoundError
)


router = APIRouter(prefix="/permission-requests", tags=["Permission Requests"])


async def get_permission_request_service(
    db: AsyncSession = Depends(get_async_db)
) -> PermissionRequestService:
    """Dependency to get PermissionRequestService"""
    client_assignment_service = ClientAssignmentService(db)
    google_api_service = GoogleApiService()
    audit_service = AuditService(db)
    
    return PermissionRequestService(
        db=db,
        client_assignment_service=client_assignment_service,
        google_api_service=google_api_service,
        audit_service=audit_service
    )


@router.get("/clients/{client_id}/properties", response_model=ClientPropertiesResponse)
async def get_client_properties(
    client_id: int,
    current_user: User = Depends(get_current_user),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Get GA4 properties available for a client
    
    Returns all GA4 properties that are accessible through the client's service accounts.
    User must be assigned to the client to view its properties.
    """
    try:
        return await service.get_client_available_properties(current_user.id, client_id)
    except UnauthorizedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not assigned to client {client_id}"
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/", response_model=PermissionRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_permission_request(
    request_data: PermissionRequestCreate,
    current_user: User = Depends(get_current_user),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Submit a new permission request
    
    Creates a new permission request for GA4 property access. The request may be:
    - Auto-approved (for Viewer/Analyst permissions by Requesters+)
    - Pending approval (for higher permission levels or lower user roles)
    
    Auto-approval rules:
    - Viewer/Analyst: Auto-approved for Requester+ roles
    - Marketer/Editor: Requires Admin approval
    - Administrator: Requires Super Admin approval
    """
    try:
        return await service.submit_permission_request(current_user.id, request_data)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateResourceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/auto-approval-rules")
async def get_auto_approval_rules(
    current_user: User = Depends(get_current_user)
):
    """
    Get auto-approval rules for all permission levels and the current user's role
    
    Returns information about which permission levels would be auto-approved
    for the current user's role.
    """
    from ...models.db_models import PermissionLevel
    
    rules = []
    service = PermissionRequestService(None, None, None, None)  # Only using static method
    
    for perm_level in PermissionLevel:
        rule = await service.evaluate_auto_approval(current_user.role, perm_level, 0)  # client_id not used in static evaluation
        rules.append(rule)
    
    return {"rules": rules, "user_role": current_user.role}


@router.get("/my-requests", response_model=List[PermissionRequestResponse])
async def get_my_permission_requests(
    status_filter: Optional[PermissionRequestStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Get current user's permission requests
    
    Returns a list of permission requests submitted by the current user,
    optionally filtered by status.
    """
    return await service.get_user_permission_requests(
        current_user.id, status_filter, limit, offset
    )


@router.get("/pending-approvals", response_model=List[PermissionRequestResponse])
async def get_pending_approval_requests(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Get permission requests pending approval
    
    Returns permission requests that the current user can approve based on their role:
    - Admin: Can approve requests requiring Admin or lower approval
    - Super Admin: Can approve all requests
    
    Only accessible to Admin and Super Admin users.
    """
    return await service.get_pending_requests_for_approval(
        current_user.id, limit, offset
    )


@router.put("/{request_id}/approve", response_model=PermissionRequestResponse)
async def approve_permission_request(
    request_id: int,
    processing_notes: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Approve a permission request
    
    Approves the specified permission request and creates the corresponding
    permission grant. The GA4 permission will be granted asynchronously.
    
    Only accessible to Admin and Super Admin users with sufficient role level.
    """
    try:
        return await service.approve_permission_request(
            request_id, current_user.id, processing_notes
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{request_id}/reject", response_model=PermissionRequestResponse)
async def reject_permission_request(
    request_id: int,
    rejection_data: dict,  # {"processing_notes": "reason for rejection"}
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Reject a permission request
    
    Rejects the specified permission request with a reason.
    Processing notes are required for rejections.
    
    Only accessible to Admin and Super Admin users.
    """
    processing_notes = rejection_data.get("processing_notes")
    if not processing_notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Processing notes are required for rejections"
        )
    
    try:
        return await service.reject_permission_request(
            request_id, current_user.id, processing_notes
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{request_id}", response_model=PermissionRequestResponse)
async def get_permission_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Get a specific permission request
    
    Returns details of a specific permission request. Users can only view:
    - Their own permission requests
    - Requests they can approve (Admin/Super Admin)
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from ...models.db_models import PermissionRequest
    
    db = service.db
    
    # Get the permission request
    query = select(PermissionRequest).where(PermissionRequest.id == request_id)
    result = await db.execute(query)
    permission_request = result.scalar_one_or_none()
    
    if not permission_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission request {request_id} not found"
        )
    
    # Check access permissions
    can_view = False
    
    # Users can view their own requests
    if permission_request.user_id == current_user.id:
        can_view = True
    
    # Admins and Super Admins can view requests they can approve
    elif current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if current_user.role == UserRole.SUPER_ADMIN:
            can_view = True  # Super Admin can view all
        elif current_user.role == UserRole.ADMIN and permission_request.requires_approval_from_role == UserRole.ADMIN:
            can_view = True
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view this request"
        )
    
    return await service._build_permission_request_response(permission_request)


@router.delete("/{request_id}", response_model=MessageResponse)
async def cancel_permission_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    service: PermissionRequestService = Depends(get_permission_request_service)
):
    """
    Cancel a pending permission request
    
    Users can only cancel their own pending permission requests.
    Auto-approved and processed requests cannot be cancelled.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from ...models.db_models import PermissionRequest
    
    db = service.db
    
    # Get the permission request
    query = select(PermissionRequest).where(
        PermissionRequest.id == request_id,
        PermissionRequest.user_id == current_user.id
    )
    result = await db.execute(query)
    permission_request = result.scalar_one_or_none()
    
    if not permission_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission request {request_id} not found or not owned by current user"
        )
    
    if permission_request.status != PermissionRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel permission request with status: {permission_request.status.value}"
        )
    
    # Update status to cancelled
    permission_request.status = PermissionRequestStatus.CANCELLED
    permission_request.processed_at = datetime.utcnow()
    permission_request.processed_by_id = current_user.id
    permission_request.processing_notes = "Cancelled by user"
    
    await db.commit()
    
    # Log the action
    await service.audit_service.log_action(
        actor_id=current_user.id,
        action="cancel_permission_request",
        resource_type="permission_request",
        resource_id=str(request_id),
        details={"reason": "cancelled_by_user"}
    )
    
    return MessageResponse(message=f"Permission request {request_id} cancelled successfully")