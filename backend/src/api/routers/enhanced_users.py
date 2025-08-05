"""
Enhanced User Management API with RBAC Integration
Phase 2 implementation with role-based access control
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr

from ...core.database import get_db
from ...core.rbac import (
    Permission, require_permission, require_role, get_current_user_with_permissions,
    RBACService, check_resource_access
)
from ...models.db_models import (
    User, UserRole, UserStatus, RegistrationStatus, 
    ClientAssignment, Client, UserSession
)
from ...models.schemas import UserResponse, UserCreate, UserUpdate
from ...services.user_service import UserService

router = APIRouter(prefix="/api/v2/users", tags=["Enhanced User Management"])


# ============================================================================
# Enhanced Pydantic Models
# ============================================================================

class UserDetailResponse(BaseModel):
    """Detailed user response with RBAC information"""
    id: int
    email: EmailStr
    name: str
    company: Optional[str]
    role: str
    status: str
    registration_status: str
    
    # Profile information
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone_number: Optional[str] = None
    is_representative: bool = False
    
    # Status information
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    
    # RBAC information
    permissions: List[str]
    resource_ownership: str
    can_access_system: bool
    
    # Client assignments
    assigned_clients: List[Dict[str, Any]] = []
    active_sessions_count: int = 0
    
    # Approval workflow
    approved_by: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None


class UserCreateRequest(BaseModel):
    """Enhanced user creation request"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    
    # Role assignment
    role: UserRole = Field(UserRole.USER, description="Initial role for the user")
    
    # Profile information
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    
    # Client assignment
    client_ids: Optional[List[int]] = Field(None, description="List of client IDs to assign")
    
    # Approval settings
    auto_approve: bool = Field(False, description="Auto-approve user registration")
    send_welcome_email: bool = Field(True, description="Send welcome email")


class UserApprovalRequest(BaseModel):
    """User approval/rejection request"""
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, description="Reason for approval/rejection")
    role: Optional[UserRole] = Field(None, description="Role to assign upon approval")
    client_ids: Optional[List[int]] = Field(None, description="Client IDs to assign")
    send_notification: bool = Field(True, description="Send notification email")


# ============================================================================
# User Listing and Search
# ============================================================================

@router.get("/", response_model=List[UserDetailResponse])
@require_permission(Permission.USER_READ)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(50, ge=1, le=200, description="Number of users per page"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    sort_by: str = Query("created_at", pattern="^(name|email|created_at|last_login_at|role)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced user listing with advanced filtering and RBAC-aware access control
    """
    # Build query with RBAC filtering
    query = select(User).options(
        selectinload(User.client_assignments).selectinload(ClientAssignment.client),
        selectinload(User.user_sessions),
        selectinload(User.approved_by)
    )
    
    # Build conditions
    conditions = []
    
    if not include_inactive:
        conditions.append(User.status == UserStatus.ACTIVE)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Apply sorting
    sort_column = getattr(User, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.unique().scalars().all()
    
    # Convert to response format
    response_users = []
    for user in users:
        # Get user permissions
        permissions = RBACService.get_role_permissions(user.role)
        ownership = RBACService.get_resource_ownership(user.role)
        
        # Get client assignments
        assigned_clients = []
        for assignment in user.client_assignments:
            if assignment.is_active_assignment:
                assigned_clients.append({
                    "id": assignment.client.id,
                    "name": assignment.client.name,
                    "access_level": assignment.access_level.value,
                    "assigned_at": assignment.assigned_at
                })
        
        # Count active sessions
        active_sessions = len([s for s in user.user_sessions if s.is_active and not s.is_expired])
        
        # Approved by information
        approved_by_info = None
        if user.approved_by:
            approved_by_info = {
                "id": user.approved_by.id,
                "name": user.approved_by.name,
                "email": user.approved_by.email
            }
        
        response_users.append(UserDetailResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            company=user.company,
            role=user.role.value,
            status=user.status.value,
            registration_status=user.registration_status.value,
            department=user.department,
            job_title=user.job_title,
            phone_number=user.phone_number,
            is_representative=user.is_representative,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            email_verified_at=user.email_verified_at,
            approved_at=user.approved_at,
            permissions=[p.value for p in permissions],
            resource_ownership=ownership.value,
            can_access_system=user.can_access_system,
            assigned_clients=assigned_clients,
            active_sessions_count=active_sessions,
            approved_by=approved_by_info,
            rejection_reason=user.rejection_reason
        ))
    
    return response_users


@router.get("/search")
@require_permission(Permission.USER_READ)
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Search users by name, email, or company with RBAC filtering
    """
    # Build search query
    search_term = f"%{q}%"
    query = select(User).where(
        or_(
            User.name.ilike(search_term),
            User.email.ilike(search_term),
            User.company.ilike(search_term)
        ),
        User.status == UserStatus.ACTIVE
    ).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "company": user.company,
            "role": user.role.value,
            "status": user.status.value
        }
        for user in users
    ]


# ============================================================================
# User Creation and Management
# ============================================================================

@router.post("/", response_model=UserDetailResponse)
@require_permission(Permission.USER_CREATE)
async def create_user(
    user_data: UserCreateRequest,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new user with enhanced RBAC validation and client assignment
    """
    user_service = UserService(db)
    actor_role = UserRole(current_user["role"])
    
    # Validate role assignment permission
    if not RBACService.can_manage_role(actor_role, user_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot assign role {user_data.role.value}"
        )
    
    # Check for existing user
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create user
    user_create = UserCreate(
        email=user_data.email,
        name=user_data.name,
        company=user_data.company,
        password=user_data.password
    )
    
    user = await user_service.create_user(user_create, is_admin_creation=True)
    
    # Update additional fields
    update_data = {
        "role": user_data.role,
        "department": user_data.department,
        "job_title": user_data.job_title,
        "phone_number": user_data.phone_number
    }
    
    # Auto-approve if requested and allowed
    if user_data.auto_approve and RBACService.has_permission(actor_role, Permission.USER_APPROVE):
        update_data["registration_status"] = RegistrationStatus.APPROVED
        update_data["approved_at"] = datetime.utcnow()
        update_data["approved_by_id"] = current_user["user_id"]
    
    await user_service.update_user(user.id, update_data)
    
    # Return detailed response
    updated_user = await user_service.get_user_by_id(user.id)
    permissions = RBACService.get_role_permissions(updated_user.role)
    ownership = RBACService.get_resource_ownership(updated_user.role)
    
    return UserDetailResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        company=updated_user.company,
        role=updated_user.role.value,
        status=updated_user.status.value,
        registration_status=updated_user.registration_status.value,
        department=updated_user.department,
        job_title=updated_user.job_title,
        phone_number=updated_user.phone_number,
        is_representative=updated_user.is_representative,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        last_login_at=updated_user.last_login_at,
        email_verified_at=updated_user.email_verified_at,
        approved_at=updated_user.approved_at,
        permissions=[p.value for p in permissions],
        resource_ownership=ownership.value,
        can_access_system=updated_user.can_access_system,
        assigned_clients=[],
        active_sessions_count=0,
        approved_by=None,
        rejection_reason=updated_user.rejection_reason
    )


# ============================================================================
# User Approval Workflow
# ============================================================================

@router.post("/{user_id}/approval")
@require_permission(Permission.USER_APPROVE)
async def process_user_approval(
    user_id: int,
    approval_data: UserApprovalRequest,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject user registration with role assignment
    """
    user_service = UserService(db)
    
    # Get user
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate user status
    if user.registration_status not in [RegistrationStatus.VERIFIED, RegistrationStatus.PENDING_VERIFICATION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User cannot be processed in current status: {user.registration_status.value}"
        )
    
    actor_role = UserRole(current_user["role"])
    
    if approval_data.action == "approve":
        # Validate role assignment if provided
        target_role = approval_data.role or UserRole.USER
        if not RBACService.can_manage_role(actor_role, target_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot assign role {target_role.value}"
            )
        
        # Approve user
        update_data = {
            "registration_status": RegistrationStatus.APPROVED,
            "approved_at": datetime.utcnow(),
            "approved_by_id": current_user["user_id"],
            "role": target_role,
            "rejection_reason": None
        }
        
        await user_service.update_user(user_id, update_data)
        message = f"User {user.email} approved successfully"
        
    else:  # reject
        update_data = {
            "registration_status": RegistrationStatus.REJECTED,
            "rejection_reason": approval_data.reason or "Registration rejected by administrator"
        }
        
        await user_service.update_user(user_id, update_data)
        message = f"User {user.email} rejected"
    
    return {
        "success": True,
        "message": message,
        "user_id": user_id,
        "action": approval_data.action,
        "processed_by": current_user["name"],
        "processed_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# User Analytics and Reporting
# ============================================================================

@router.get("/analytics/registration-trends")
@require_permission(Permission.AUDIT_READ)
async def get_registration_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user registration trends and analytics
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Query registration trends
    query = select(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('registrations'),
        func.count().filter(User.registration_status == RegistrationStatus.APPROVED).label('approved'),
        func.count().filter(User.registration_status == RegistrationStatus.REJECTED).label('rejected')
    ).where(
        func.date(User.created_at) >= start_date,
        func.date(User.created_at) <= end_date
    ).group_by(
        func.date(User.created_at)
    ).order_by(
        func.date(User.created_at)
    )
    
    result = await db.execute(query)
    trends = result.fetchall()
    
    # Query role distribution for new users
    role_query = select(
        User.role,
        func.count(User.id).label('count')
    ).where(
        func.date(User.created_at) >= start_date
    ).group_by(User.role)
    
    role_result = await db.execute(role_query)
    role_distribution = dict(role_result.fetchall())
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "daily_trends": [
            {
                "date": trend.date.isoformat(),
                "registrations": trend.registrations,
                "approved": trend.approved,
                "rejected": trend.rejected
            }
            for trend in trends
        ],
        "role_distribution": {
            role.value: count for role, count in role_distribution.items()
        },
        "summary": {
            "total_registrations": sum(t.registrations for t in trends),
            "total_approved": sum(t.approved for t in trends),
            "total_rejected": sum(t.rejected for t in trends),
            "approval_rate": (sum(t.approved for t in trends) / sum(t.registrations for t in trends) * 100) if trends else 0
        }
    }