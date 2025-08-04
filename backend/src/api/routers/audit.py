"""
Audit logs API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional, Dict, Any
from datetime import datetime

from ...core.database import get_db
from ...models.schemas import AuditLogResponse
from ...services.auth_service import AuthService
from ...services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    actor_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """List audit logs"""
    # Only admins can view audit logs
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    audit_service = AuditService(db)
    logs = await audit_service.get_audit_logs(
        skip=skip,
        limit=limit,
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
        start_date=start_date,
        end_date=end_date
    )
    return logs


@router.get("/recent", response_model=List[AuditLogResponse])
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    resource_types: Optional[List[str]] = Query(None),
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get recent activity logs"""
    audit_service = AuditService(db)
    logs = await audit_service.get_recent_activity(
        limit=limit,
        resource_types=resource_types
    )
    return logs


@router.get("/summary", response_model=Dict[str, Any])
async def get_activity_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get activity summary statistics"""
    # Only admins can view audit summaries
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    audit_service = AuditService(db)
    summary = await audit_service.get_activity_summary(
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/count")
async def count_audit_logs(
    actor_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Count audit logs with filters"""
    # Only admins can count audit logs
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    audit_service = AuditService(db)
    count = await audit_service.count_audit_logs(
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
        start_date=start_date,
        end_date=end_date
    )
    return {"count": count}