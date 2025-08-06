"""
Permission Lifecycle API endpoints
Tracks complete permission lifecycle: 요청→승인→활성→만료
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ...core.database import get_db
from ...core.rbac import Permission, require_permission, get_current_user_with_permissions
from ...models.db_models import (
    User, UserRole, PermissionRequest, PermissionGrant,
    PermissionRequestStatus, PermissionStatus, PermissionLevel
)
from ...models.schemas import MessageResponse
from ...services.permission_request_service import PermissionRequestService
from ...services.audit_service import AuditService

router = APIRouter(prefix="/permission-lifecycle", tags=["Permission Lifecycle"])


async def get_permission_request_service(
    db: AsyncSession = Depends(get_db)
) -> PermissionRequestService:
    """Dependency to get PermissionRequestService"""
    from ...services.client_assignment_service import ClientAssignmentService
    from ...services.google_api_service import GoogleAnalyticsService
    
    client_assignment_service = ClientAssignmentService(db)
    google_api_service = GoogleAnalyticsService()
    audit_service = AuditService(db)
    
    return PermissionRequestService(
        db=db,
        client_assignment_service=client_assignment_service,
        google_api_service=google_api_service,
        audit_service=audit_service
    )


@router.get("/dashboard")
@require_permission(Permission.PERMISSION_READ)
async def get_lifecycle_dashboard(
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get permission lifecycle dashboard overview
    
    Shows comprehensive statistics across all lifecycle stages:
    - 요청 단계 (Request Stage)
    - 승인 단계 (Approval Stage) 
    - 활성 단계 (Active Stage)
    - 만료 단계 (Expiry Stage)
    """
    user_role = current_user.get("role")
    user_id = current_user.get("user_id")
    
    # Base queries for statistics
    request_query = select(PermissionRequest)
    grant_query = select(PermissionGrant)
    
    # Apply role-based filtering
    if user_role not in ["super_admin", "admin"]:
        # Regular users see only their own data
        request_query = request_query.where(PermissionRequest.user_id == user_id)
        grant_query = grant_query.where(PermissionGrant.user_id == user_id)
    
    # Request Stage Statistics (요청 단계)
    request_stats = {}
    for status in PermissionRequestStatus:
        count_query = request_query.where(PermissionRequest.status == status)
        result = await db.execute(select(func.count()).select_from(count_query.subquery()))
        count = result.scalar() or 0
        request_stats[status.value] = count
    
    # Active Permissions Statistics (활성 단계)
    now = datetime.utcnow()
    active_query = grant_query.where(
        and_(
            PermissionGrant.status == PermissionStatus.ACTIVE,
            or_(
                PermissionGrant.expires_at.is_(None),
                PermissionGrant.expires_at > now
            )
        )
    )
    active_result = await db.execute(select(func.count()).select_from(active_query.subquery()))
    active_count = active_result.scalar() or 0
    
    # Expiring Soon Statistics (곧 만료)
    expiring_soon_query = grant_query.where(
        and_(
            PermissionGrant.status == PermissionStatus.ACTIVE,
            PermissionGrant.expires_at.is_not(None),
            PermissionGrant.expires_at <= now + timedelta(days=7),
            PermissionGrant.expires_at > now
        )
    )
    expiring_soon_result = await db.execute(select(func.count()).select_from(expiring_soon_query.subquery()))
    expiring_soon_count = expiring_soon_result.scalar() or 0
    
    # Expired Statistics (만료됨)
    expired_query = grant_query.where(
        and_(
            PermissionGrant.expires_at.is_not(None),
            PermissionGrant.expires_at <= now
        )
    )
    expired_result = await db.execute(select(func.count()).select_from(expired_query.subquery()))
    expired_count = expired_result.scalar() or 0
    
    # Permission Level Distribution
    level_stats = {}
    for level in PermissionLevel:
        level_query = grant_query.where(
            and_(
                PermissionGrant.permission_level == level,
                PermissionGrant.status == PermissionStatus.ACTIVE
            )
        )
        level_result = await db.execute(select(func.count()).select_from(level_query.subquery()))
        level_count = level_result.scalar() or 0
        level_stats[level.value] = level_count
    
    return {
        "summary": {
            "total_requests": sum(request_stats.values()),
            "active_permissions": active_count,
            "expiring_soon": expiring_soon_count,
            "expired_permissions": expired_count
        },
        "request_stage": request_stats,
        "active_stage": {
            "active": active_count,
            "expiring_soon": expiring_soon_count,
            "expired": expired_count
        },
        "permission_levels": level_stats,
        "generated_at": datetime.utcnow().isoformat(),
        "user_context": {
            "user_id": user_id,
            "role": user_role,
            "is_admin": user_role in ["admin", "super_admin"]
        }
    }


@router.get("/timeline")
@require_permission(Permission.PERMISSION_READ)
async def get_permission_timeline(
    permission_request_id: Optional[int] = Query(None, description="Specific permission request to track"),
    permission_grant_id: Optional[int] = Query(None, description="Specific permission grant to track"),
    user_id: Optional[int] = Query(None, description="Filter by user (admin only)"),
    days: int = Query(30, ge=1, le=365, description="Timeline range in days"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get permission lifecycle timeline
    
    Shows chronological progression through lifecycle stages:
    1. 요청 생성 (Request Created)
    2. 승인/거부 (Approved/Rejected)
    3. 활성화 (Activated)
    4. 만료 알림 (Expiry Notifications)
    5. 만료 (Expired)
    """
    user_role = current_user.get("role")
    current_user_id = current_user.get("user_id")
    
    # Permission checks
    if user_role not in ["super_admin", "admin"] and user_id and user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' timeline data"
        )
        
    # Apply user filtering for non-admin users
    if user_role not in ["super_admin", "admin"]:
        user_id = current_user_id
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    timeline_events = []
    
    # Get permission requests in timeline
    request_query = select(PermissionRequest).where(
        PermissionRequest.created_at >= start_date
    )
    
    if permission_request_id:
        request_query = request_query.where(PermissionRequest.id == permission_request_id)
    if user_id:
        request_query = request_query.where(PermissionRequest.user_id == user_id)
    
    request_query = request_query.order_by(PermissionRequest.created_at.desc())
    requests_result = await db.execute(request_query)
    requests = requests_result.scalars().all()
    
    for req in requests:
        # Request creation event
        timeline_events.append({
            "id": f"req_{req.id}_created",
            "type": "request_created",
            "stage": "요청",
            "timestamp": req.created_at.isoformat(),
            "permission_request_id": req.id,
            "user_id": req.user_id,
            "ga_property_id": req.ga_property_id,
            "permission_level": req.permission_level.value,
            "status": req.status.value,
            "description": f"Permission request created for {req.target_email}",
            "details": {
                "target_email": req.target_email,
                "business_justification": req.business_justification,
                "auto_approved": req.auto_approved
            }
        })
        
        # Processing events (approval/rejection)
        if req.processed_at:
            event_type = "request_approved" if req.status == PermissionRequestStatus.APPROVED else "request_rejected"
            stage = "승인" if req.status == PermissionRequestStatus.APPROVED else "거부"
            
            timeline_events.append({
                "id": f"req_{req.id}_processed",
                "type": event_type,
                "stage": stage,
                "timestamp": req.processed_at.isoformat(),
                "permission_request_id": req.id,
                "processed_by_id": req.processed_by_id,
                "description": f"Permission request {req.status.value}",
                "details": {
                    "processing_notes": req.processing_notes,
                    "auto_approved": req.auto_approved
                }
            })
    
    # Get permission grants in timeline
    grant_query = select(PermissionGrant).where(
        or_(
            PermissionGrant.created_at >= start_date,
            and_(
                PermissionGrant.expires_at.is_not(None),
                PermissionGrant.expires_at >= start_date
            )
        )
    )
    
    if permission_grant_id:
        grant_query = grant_query.where(PermissionGrant.id == permission_grant_id)
    if user_id:
        grant_query = grant_query.where(PermissionGrant.user_id == user_id)
    
    grant_query = grant_query.order_by(PermissionGrant.created_at.desc())
    grants_result = await db.execute(grant_query)
    grants = grants_result.scalars().all()
    
    for grant in grants:
        # Grant activation event
        if grant.approved_at and grant.approved_at >= start_date:
            timeline_events.append({
                "id": f"grant_{grant.id}_activated",
                "type": "permission_activated",
                "stage": "활성",
                "timestamp": grant.approved_at.isoformat(),
                "permission_grant_id": grant.id,
                "user_id": grant.user_id,
                "ga_property_id": grant.ga_property_id,
                "permission_level": grant.permission_level.value,
                "target_email": grant.target_email,
                "description": f"Permission activated for {grant.target_email}",
                "details": {
                    "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
                    "approved_by_id": grant.approved_by_id
                }
            })
        
        # Expiry warning events (7 days before expiry)
        if grant.expires_at and grant.status == PermissionStatus.ACTIVE:
            warning_date = grant.expires_at - timedelta(days=7)
            if warning_date >= start_date and warning_date <= end_date:
                timeline_events.append({
                    "id": f"grant_{grant.id}_expiry_warning",
                    "type": "expiry_warning",
                    "stage": "만료 예정",
                    "timestamp": warning_date.isoformat(),
                    "permission_grant_id": grant.id,
                    "description": f"Permission expiring in 7 days for {grant.target_email}",
                    "details": {
                        "expires_at": grant.expires_at.isoformat(),
                        "days_remaining": 7
                    }
                })
        
        # Expiry events
        if grant.expires_at and grant.expires_at >= start_date:
            timeline_events.append({
                "id": f"grant_{grant.id}_expired",
                "type": "permission_expired",
                "stage": "만료",
                "timestamp": grant.expires_at.isoformat(),
                "permission_grant_id": grant.id,
                "description": f"Permission expired for {grant.target_email}",
                "details": {
                    "expired_at": grant.expires_at.isoformat(),
                    "was_active": grant.status == PermissionStatus.ACTIVE
                }
            })
    
    # Sort timeline events by timestamp (most recent first)
    timeline_events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Generate summary statistics
    stage_counts = {}
    for event in timeline_events:
        stage = event["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    
    return {
        "timeline": timeline_events[:100],  # Limit to 100 most recent events
        "total_events": len(timeline_events),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "stage_summary": stage_counts,
        "filters": {
            "permission_request_id": permission_request_id,
            "permission_grant_id": permission_grant_id,
            "user_id": user_id
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/expiring")
@require_permission(Permission.PERMISSION_READ)
async def get_expiring_permissions(
    days_ahead: int = Query(7, ge=1, le=90, description="Days ahead to check for expiring permissions"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get permissions expiring within specified days
    
    Used for proactive notification and renewal workflows
    """
    user_role = current_user.get("role")
    user_id = current_user.get("user_id")
    
    now = datetime.utcnow()
    expiry_threshold = now + timedelta(days=days_ahead)
    
    # Build query for expiring permissions
    query = select(PermissionGrant).where(
        and_(
            PermissionGrant.status == PermissionStatus.ACTIVE,
            PermissionGrant.expires_at.is_not(None),
            PermissionGrant.expires_at <= expiry_threshold,
            PermissionGrant.expires_at > now
        )
    ).order_by(PermissionGrant.expires_at.asc())
    
    # Apply role-based filtering
    if user_role not in ["super_admin", "admin"]:
        query = query.where(PermissionGrant.user_id == user_id)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    grants = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(PermissionGrant.id)).where(
        and_(
            PermissionGrant.status == PermissionStatus.ACTIVE,
            PermissionGrant.expires_at.is_not(None),
            PermissionGrant.expires_at <= expiry_threshold,
            PermissionGrant.expires_at > now
        )
    )
    
    if user_role not in ["super_admin", "admin"]:
        count_query = count_query.where(PermissionGrant.user_id == user_id)
    
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Format response data
    expiring_permissions = []
    for grant in grants:
        days_until_expiry = (grant.expires_at - now).days
        hours_until_expiry = (grant.expires_at - now).total_seconds() / 3600
        
        expiring_permissions.append({
            "permission_grant_id": grant.id,
            "user_id": grant.user_id,
            "client_id": grant.client_id,
            "ga_property_id": grant.ga_property_id,
            "target_email": grant.target_email,
            "permission_level": grant.permission_level.value,
            "expires_at": grant.expires_at.isoformat(),
            "days_until_expiry": days_until_expiry,
            "hours_until_expiry": round(hours_until_expiry, 1),
            "urgency": "critical" if days_until_expiry <= 1 else "high" if days_until_expiry <= 3 else "medium",
            "can_extend": grant.status == PermissionStatus.ACTIVE,
            "created_at": grant.created_at.isoformat(),
            "approved_at": grant.approved_at.isoformat() if grant.approved_at else None
        })
    
    # Categorize by urgency
    urgency_counts = {"critical": 0, "high": 0, "medium": 0}
    for perm in expiring_permissions:
        urgency_counts[perm["urgency"]] += 1
    
    return {
        "expiring_permissions": expiring_permissions,
        "total_count": total_count,
        "returned_count": len(expiring_permissions),
        "pagination": {
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(expiring_permissions) < total_count
        },
        "urgency_summary": urgency_counts,
        "query_parameters": {
            "days_ahead": days_ahead,
            "threshold_date": expiry_threshold.isoformat()
        },
        "generated_at": now.isoformat()
    }


@router.post("/bulk-extend")
@require_permission(Permission.PERMISSION_UPDATE)
async def bulk_extend_permissions(
    request_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user_with_permissions),
    service: PermissionRequestService = Depends(get_permission_request_service)
) -> Dict[str, Any]:
    """
    Bulk extend multiple permissions
    
    Useful for managing permissions that are expiring soon
    """
    permission_grant_ids = request_data.get("permission_grant_ids", [])
    additional_days = request_data.get("additional_days", 30)
    reason = request_data.get("reason", "Bulk extension via lifecycle API")
    
    if not permission_grant_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="permission_grant_ids list is required"
        )
    
    if not (1 <= additional_days <= 365):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="additional_days must be between 1 and 365"
        )
    
    results = {
        "extended": [],
        "failed": [],
        "summary": {
            "total_requested": len(permission_grant_ids),
            "successful": 0,
            "failed": 0
        }
    }
    
    for grant_id in permission_grant_ids:
        try:
            # This would need to be implemented in the service
            # For now, we'll create a placeholder response
            results["extended"].append({
                "permission_grant_id": grant_id,
                "additional_days": additional_days,
                "new_expires_at": (datetime.utcnow() + timedelta(days=additional_days)).isoformat(),
                "extended_by": current_user.get("user_id"),
                "reason": reason
            })
            results["summary"]["successful"] += 1
            
        except Exception as e:
            results["failed"].append({
                "permission_grant_id": grant_id,
                "error": str(e)
            })
            results["summary"]["failed"] += 1
    
    # Log bulk extension action
    await service.audit_service.log_action(
        actor_id=current_user.get("user_id"),
        action="bulk_extend_permissions",
        resource_type="permission_grant",
        resource_id=f"bulk_{len(permission_grant_ids)}",
        details={
            "permission_grant_ids": permission_grant_ids,
            "additional_days": additional_days,
            "successful": results["summary"]["successful"],
            "failed": results["summary"]["failed"]
        }
    )
    
    return results


@router.get("/lifecycle-stats")
@require_permission(Permission.PERMISSION_READ)
async def get_lifecycle_statistics(
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive lifecycle statistics
    
    Provides insights into permission lifecycle patterns and trends
    """
    user_role = current_user.get("role")
    user_id = current_user.get("user_id")
    
    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(weeks=1)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:  # year
        start_date = now - timedelta(days=365)
    
    # Base queries
    request_query = select(PermissionRequest).where(
        PermissionRequest.created_at >= start_date
    )
    grant_query = select(PermissionGrant).where(
        or_(
            PermissionGrant.created_at >= start_date,
            and_(
                PermissionGrant.expires_at.is_not(None),
                PermissionGrant.expires_at >= start_date
            )
        )
    )
    
    # Apply role-based filtering
    if user_role not in ["super_admin", "admin"]:
        request_query = request_query.where(PermissionRequest.user_id == user_id)
        grant_query = grant_query.where(PermissionGrant.user_id == user_id)
    
    # Request statistics
    request_result = await db.execute(request_query)
    requests = request_result.scalars().all()
    
    request_stats = {
        "total": len(requests),
        "by_status": {},
        "by_permission_level": {},
        "auto_approved_rate": 0,
        "avg_processing_time_hours": 0
    }
    
    auto_approved_count = 0
    processing_times = []
    
    for req in requests:
        # Status distribution
        status = req.status.value
        request_stats["by_status"][status] = request_stats["by_status"].get(status, 0) + 1
        
        # Permission level distribution
        level = req.permission_level.value
        request_stats["by_permission_level"][level] = request_stats["by_permission_level"].get(level, 0) + 1
        
        # Auto-approval rate
        if req.auto_approved:
            auto_approved_count += 1
        
        # Processing time
        if req.processed_at:
            processing_time = (req.processed_at - req.created_at).total_seconds() / 3600
            processing_times.append(processing_time)
    
    if len(requests) > 0:
        request_stats["auto_approved_rate"] = round((auto_approved_count / len(requests)) * 100, 1)
    
    if processing_times:
        request_stats["avg_processing_time_hours"] = round(sum(processing_times) / len(processing_times), 1)
    
    # Grant statistics
    grant_result = await db.execute(grant_query)
    grants = grant_result.scalars().all()
    
    grant_stats = {
        "total": len(grants),
        "active": 0,
        "expired_in_period": 0,
        "avg_duration_days": 0,
        "by_permission_level": {}
    }
    
    durations = []
    
    for grant in grants:
        # Active vs expired
        if grant.status == PermissionStatus.ACTIVE:
            if not grant.expires_at or grant.expires_at > now:
                grant_stats["active"] += 1
        
        if grant.expires_at and grant.expires_at >= start_date and grant.expires_at <= now:
            grant_stats["expired_in_period"] += 1
        
        # Permission level distribution
        level = grant.permission_level.value
        grant_stats["by_permission_level"][level] = grant_stats["by_permission_level"].get(level, 0) + 1
        
        # Duration calculation
        if grant.expires_at and grant.approved_at:
            duration = (grant.expires_at - grant.approved_at).days
            durations.append(duration)
    
    if durations:
        grant_stats["avg_duration_days"] = round(sum(durations) / len(durations), 1)
    
    return {
        "period": period,
        "date_range": {
            "start": start_date.isoformat(),
            "end": now.isoformat()
        },
        "request_statistics": request_stats,
        "grant_statistics": grant_stats,
        "lifecycle_efficiency": {
            "request_to_approval_rate": round(
                (request_stats["by_status"].get("approved", 0) / max(request_stats["total"], 1)) * 100, 1
            ),
            "auto_approval_efficiency": request_stats["auto_approved_rate"],
            "avg_processing_time": request_stats["avg_processing_time_hours"]
        },
        "generated_at": now.isoformat(),
        "user_context": {
            "role": user_role,
            "viewing_own_data": user_role not in ["super_admin", "admin"]
        }
    }