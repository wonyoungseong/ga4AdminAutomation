"""
Audit logging service
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.db_models import AuditLog
from ..models.schemas import AuditLogResponse


class AuditService:
    """Audit logging service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        action: str,
        resource_type: str,
        actor_id: Optional[int] = None,
        permission_grant_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an action to the audit trail"""
        
        audit_log = AuditLog(
            actor_id=actor_id,
            permission_grant_id=permission_grant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        return audit_log
    
    async def log_permission_action(
        self,
        action: str,
        permission_grant_id: int,
        actor_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a permission-related action"""
        
        details_json = json.dumps(details) if details else None
        
        return await self.log_action(
            action=action,
            resource_type="permission_grant",
            actor_id=actor_id,
            permission_grant_id=permission_grant_id,
            resource_id=str(permission_grant_id),
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_user_action(
        self,
        action: str,
        user_id: int,
        actor_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log a user-related action"""
        
        details_json = json.dumps(details) if details else None
        
        return await self.log_action(
            action=action,
            resource_type="user",
            actor_id=actor_id,
            resource_id=str(user_id),
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_authentication_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an authentication-related action"""
        
        details_json = json.dumps(details) if details else None
        
        return await self.log_action(
            action=action,
            resource_type="authentication",
            actor_id=user_id,
            resource_id=str(user_id) if user_id else None,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        actor_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogResponse]:
        """Get audit logs with optional filters"""
        
        query = select(AuditLog)
        
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if action:
            query = query.where(AuditLog.action == action)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        query = query.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [AuditLogResponse.model_validate(log) for log in logs]
    
    async def get_recent_activity(
        self,
        limit: int = 10,
        resource_types: Optional[List[str]] = None
    ) -> List[AuditLogResponse]:
        """Get recent activity logs"""
        
        query = select(AuditLog)
        
        if resource_types:
            query = query.where(AuditLog.resource_type.in_(resource_types))
        
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [AuditLogResponse.model_validate(log) for log in logs]
    
    async def count_audit_logs(
        self,
        actor_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count audit logs with optional filters"""
        
        query = select(func.count(AuditLog.id))
        
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if action:
            query = query.where(AuditLog.action == action)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def get_activity_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get activity summary statistics"""
        
        # Base query
        base_query = select(AuditLog)
        if start_date:
            base_query = base_query.where(AuditLog.created_at >= start_date)
        if end_date:
            base_query = base_query.where(AuditLog.created_at <= end_date)
        
        # Total actions
        total_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(
                base_query.whereclause if hasattr(base_query, 'whereclause') else True
            )
        )
        total_actions = total_result.scalar()
        
        # Actions by type
        type_result = await self.db.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id))
            .where(base_query.whereclause if hasattr(base_query, 'whereclause') else True)
            .group_by(AuditLog.resource_type)
        )
        actions_by_type = dict(type_result.fetchall())
        
        # Actions by action
        action_result = await self.db.execute(
            select(AuditLog.action, func.count(AuditLog.id))
            .where(base_query.whereclause if hasattr(base_query, 'whereclause') else True)
            .group_by(AuditLog.action)
        )
        actions_by_action = dict(action_result.fetchall())
        
        return {
            "total_actions": total_actions,
            "actions_by_type": actions_by_type,
            "actions_by_action": actions_by_action,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }