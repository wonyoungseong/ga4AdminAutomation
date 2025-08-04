"""
Report generation and download tracking service - Legacy compatible
"""

import json
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError, AuthorizationError
from ..models.db_models import (
    ReportDownloadLog, User, UserPermission, PermissionGrant, 
    GA4Property, Client, AuditLog,
    ReportType, UserRole, PermissionStatus
)
from ..models.schemas import ReportDownloadLogResponse, SystemMetricsResponse
from ..services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Report generation and download tracking service - Legacy compatible"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
    
    async def generate_system_metrics_report(
        self,
        admin_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate system metrics report"""
        
        # Validate admin permissions
        admin_result = await self.db.execute(select(User).where(User.id == admin_id))
        admin = admin_result.scalar_one_or_none()
        if not admin:
            raise NotFoundError("Admin not found")
        
        if admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to generate reports")
        
        # Get system metrics
        metrics = await self._collect_system_metrics()
        
        # Create download log
        report_id = f"system_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        download_log = ReportDownloadLog(
            admin_id=admin_id,
            report_type=ReportType.SYSTEM_METRICS,
            report_id=report_id,
            report_name="System Metrics Report",
            file_format="json",
            ip_address=ip_address,
            user_agent=user_agent,
            file_size_bytes=len(json.dumps(metrics).encode('utf-8'))
        )
        
        self.db.add(download_log)
        await self.db.commit()
        
        # Log the report generation
        await self.audit_service.log_action(
            actor_id=admin_id,
            action="generate_system_metrics_report",
            resource_type="report",
            resource_id=report_id,
            details="Generated system metrics report"
        )
        
        logger.info(f"Generated system metrics report {report_id}")
        
        return {
            "report_id": report_id,
            "report_type": ReportType.SYSTEM_METRICS,
            "generated_at": datetime.utcnow(),
            "data": metrics,
            "download_log_id": download_log.id
        }
    
    async def generate_user_activity_report(
        self,
        admin_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        file_format: str = "json",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate user activity report"""
        
        # Validate admin permissions
        admin_result = await self.db.execute(select(User).where(User.id == admin_id))
        admin = admin_result.scalar_one_or_none()
        if not admin:
            raise NotFoundError("Admin not found")
        
        if admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to generate reports")
        
        # Set default date range (last 30 days)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get user activity data
        activity_data = await self._collect_user_activity_data(start_date, end_date, user_id)
        
        # Format data based on file format
        if file_format.lower() == "csv":
            formatted_data = await self._format_user_activity_csv(activity_data)
        else:
            formatted_data = activity_data
        
        # Create download log
        report_id = f"user_activity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        download_log = ReportDownloadLog(
            admin_id=admin_id,
            report_type=ReportType.USER_ACTIVITY,
            report_id=report_id,
            report_name=f"User Activity Report ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
            file_format=file_format,
            ip_address=ip_address,
            user_agent=user_agent,
            file_size_bytes=len(str(formatted_data).encode('utf-8'))
        )
        
        self.db.add(download_log)
        await self.db.commit()
        
        # Log the report generation
        await self.audit_service.log_action(
            actor_id=admin_id,
            action="generate_user_activity_report",
            resource_type="report",
            resource_id=report_id,
            details=f"Generated user activity report for period {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
        
        logger.info(f"Generated user activity report {report_id}")
        
        return {
            "report_id": report_id,
            "report_type": ReportType.USER_ACTIVITY,
            "generated_at": datetime.utcnow(),
            "period_start": start_date,
            "period_end": end_date,
            "data": formatted_data,
            "download_log_id": download_log.id
        }
    
    async def generate_permission_summary_report(
        self,
        admin_id: int,
        client_id: Optional[int] = None,
        include_expired: bool = False,
        file_format: str = "json",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate permission summary report"""
        
        # Validate admin permissions
        admin_result = await self.db.execute(select(User).where(User.id == admin_id))
        admin = admin_result.scalar_one_or_none()
        if not admin:
            raise NotFoundError("Admin not found")
        
        if admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to generate reports")
        
        # Get permission summary data
        permission_data = await self._collect_permission_summary_data(client_id, include_expired)
        
        # Format data based on file format
        if file_format.lower() == "csv":
            formatted_data = await self._format_permission_summary_csv(permission_data)
        else:
            formatted_data = permission_data
        
        # Create download log
        report_id = f"permission_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        download_log = ReportDownloadLog(
            admin_id=admin_id,
            report_type=ReportType.PERMISSION_SUMMARY,
            report_id=report_id,
            report_name="Permission Summary Report",
            file_format=file_format,
            ip_address=ip_address,
            user_agent=user_agent,
            file_size_bytes=len(str(formatted_data).encode('utf-8'))
        )
        
        self.db.add(download_log)
        await self.db.commit()
        
        # Log the report generation
        await self.audit_service.log_action(
            actor_id=admin_id,
            action="generate_permission_summary_report",
            resource_type="report",
            resource_id=report_id,
            details="Generated permission summary report"
        )
        
        logger.info(f"Generated permission summary report {report_id}")
        
        return {
            "report_id": report_id,
            "report_type": ReportType.PERMISSION_SUMMARY,
            "generated_at": datetime.utcnow(),
            "data": formatted_data,
            "download_log_id": download_log.id
        }
    
    async def generate_audit_log_report(
        self,
        admin_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_filter: Optional[str] = None,
        user_id_filter: Optional[int] = None,
        file_format: str = "json",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate audit log report"""
        
        # Validate admin permissions
        admin_result = await self.db.execute(select(User).where(User.id == admin_id))
        admin = admin_result.scalar_one_or_none()
        if not admin:
            raise NotFoundError("Admin not found")
        
        if admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise AuthorizationError("Insufficient permissions to generate reports")
        
        # Set default date range (last 30 days)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get audit log data
        audit_data = await self._collect_audit_log_data(start_date, end_date, action_filter, user_id_filter)
        
        # Format data based on file format
        if file_format.lower() == "csv":
            formatted_data = await self._format_audit_log_csv(audit_data)
        else:
            formatted_data = audit_data
        
        # Create download log
        report_id = f"audit_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        download_log = ReportDownloadLog(
            admin_id=admin_id,
            report_type=ReportType.AUDIT_LOG,
            report_id=report_id,
            report_name=f"Audit Log Report ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
            file_format=file_format,
            ip_address=ip_address,
            user_agent=user_agent,
            file_size_bytes=len(str(formatted_data).encode('utf-8'))
        )
        
        self.db.add(download_log)
        await self.db.commit()
        
        # Log the report generation
        await self.audit_service.log_action(
            actor_id=admin_id,
            action="generate_audit_log_report",
            resource_type="report",
            resource_id=report_id,
            details=f"Generated audit log report for period {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
        
        logger.info(f"Generated audit log report {report_id}")
        
        return {
            "report_id": report_id,
            "report_type": ReportType.AUDIT_LOG,
            "generated_at": datetime.utcnow(),
            "period_start": start_date,
            "period_end": end_date,
            "data": formatted_data,
            "download_log_id": download_log.id
        }
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics data"""
        
        # User counts
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.status == "active")
        )
        active_users = active_users_result.scalar()
        
        # Permission counts
        total_permissions_result = await self.db.execute(select(func.count(UserPermission.id)))
        total_permissions = total_permissions_result.scalar()
        
        active_permissions_result = await self.db.execute(
            select(func.count(UserPermission.id)).where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        active_permissions = active_permissions_result.scalar()
        
        expired_permissions_result = await self.db.execute(
            select(func.count(UserPermission.id)).where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_permissions = expired_permissions_result.scalar()
        
        expiring_soon_result = await self.db.execute(
            select(func.count(UserPermission.id)).where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= (datetime.utcnow() + timedelta(days=7)),
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        expiring_soon_permissions = expiring_soon_result.scalar()
        
        # Client counts
        total_clients_result = await self.db.execute(select(func.count(Client.id)))
        total_clients = total_clients_result.scalar()
        
        active_clients_result = await self.db.execute(
            select(func.count(Client.id)).where(Client.is_active == True)
        )
        active_clients = active_clients_result.scalar()
        
        # Property counts
        total_properties_result = await self.db.execute(select(func.count(GA4Property.id)))
        total_properties = total_properties_result.scalar()
        
        active_properties_result = await self.db.execute(
            select(func.count(GA4Property.id)).where(GA4Property.is_active == True)
        )
        active_properties = active_properties_result.scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_registrations": 0,  # TODO: Implement when user registration is added
            "total_permissions": total_permissions,
            "active_permissions": active_permissions,
            "expired_permissions": expired_permissions,
            "expiring_soon_permissions": expiring_soon_permissions,
            "total_clients": total_clients,
            "active_clients": active_clients,
            "total_properties": total_properties,
            "active_properties": active_properties,
            "daily_logins": 0,  # TODO: Implement when login tracking is added
            "failed_logins": 0,  # TODO: Implement when login tracking is added
            "generated_at": datetime.utcnow()
        }
    
    async def _collect_user_activity_data(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Collect user activity data"""
        
        query = select(User).options(selectinload(User.user_permissions))
        
        if user_id:
            query = query.where(User.id == user_id)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        activity_data = []
        for user in users:
            # Count permissions in date range
            permission_count = 0
            extension_count = 0
            
            for permission in user.user_permissions:
                if start_date <= permission.created_at <= end_date:
                    permission_count += 1
                    extension_count += permission.extension_count
            
            activity_data.append({
                "user_id": user.id,
                "user_name": user.name,
                "user_email": user.email,
                "total_login_count": 0,  # TODO: Implement when login tracking is added
                "last_login_at": user.last_login_at,
                "permission_request_count": permission_count,
                "permission_extension_count": extension_count,
                "active_permissions": len([p for p in user.user_permissions if p.is_active]),
                "created_at": user.created_at,
                "summary_period_start": start_date,
                "summary_period_end": end_date
            })
        
        return activity_data
    
    async def _collect_permission_summary_data(
        self,
        client_id: Optional[int] = None,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """Collect permission summary data"""
        
        query = select(UserPermission).options(
            selectinload(UserPermission.user),
            selectinload(UserPermission.ga_property)
        )
        
        if client_id:
            query = query.join(GA4Property).where(GA4Property.client_id == client_id)
        
        if not include_expired:
            query = query.where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        
        result = await self.db.execute(query)
        permissions = result.scalars().all()
        
        summary_data = []
        for permission in permissions:
            summary_data.append({
                "permission_id": permission.id,
                "user_name": permission.user.name,
                "user_email": permission.user.email,
                "target_email": permission.target_email,
                "property_name": permission.ga_property.property_name,
                "property_id": permission.ga_property.property_id,
                "permission_level": permission.permission_level.value,
                "status": permission.status.value,
                "granted_at": permission.granted_at,
                "expires_at": permission.expires_at,
                "extension_count": permission.extension_count,
                "is_active": permission.is_active,
                "days_until_expiry": permission.days_until_expiry,
                "revoked_at": permission.revoked_at,
                "revocation_reason": permission.revocation_reason
            })
        
        return summary_data
    
    async def _collect_audit_log_data(
        self,
        start_date: datetime,
        end_date: datetime,
        action_filter: Optional[str] = None,
        user_id_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Collect audit log data"""
        
        query = select(AuditLog).options(selectinload(AuditLog.actor))
        
        query = query.where(
            and_(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
        )
        
        if action_filter:
            query = query.where(AuditLog.action.ilike(f"%{action_filter}%"))
        
        if user_id_filter:
            query = query.where(AuditLog.actor_id == user_id_filter)
        
        query = query.order_by(AuditLog.created_at.desc())
        
        result = await self.db.execute(query)
        audit_logs = result.scalars().all()
        
        audit_data = []
        for log in audit_logs:
            audit_data.append({
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "actor_name": log.actor.name if log.actor else "System",
                "actor_email": log.actor.email if log.actor else None,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at
            })
        
        return audit_data
    
    async def _format_user_activity_csv(self, data: List[Dict[str, Any]]) -> str:
        """Format user activity data as CSV"""
        
        output = io.StringIO()
        if not data:
            return ""
        
        fieldnames = [
            "user_id", "user_name", "user_email", "total_login_count", 
            "last_login_at", "permission_request_count", "permission_extension_count",
            "active_permissions", "created_at", "summary_period_start", "summary_period_end"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    async def _format_permission_summary_csv(self, data: List[Dict[str, Any]]) -> str:
        """Format permission summary data as CSV"""
        
        output = io.StringIO()
        if not data:
            return ""
        
        fieldnames = [
            "permission_id", "user_name", "user_email", "target_email",
            "property_name", "property_id", "permission_level", "status",
            "granted_at", "expires_at", "extension_count", "is_active",
            "days_until_expiry", "revoked_at", "revocation_reason"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    async def _format_audit_log_csv(self, data: List[Dict[str, Any]]) -> str:
        """Format audit log data as CSV"""
        
        output = io.StringIO()
        if not data:
            return ""
        
        fieldnames = [
            "id", "action", "resource_type", "resource_id", "actor_name",
            "actor_email", "details", "ip_address", "user_agent", "created_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    async def get_download_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        admin_id: Optional[int] = None,
        report_type: Optional[ReportType] = None
    ) -> List[ReportDownloadLogResponse]:
        """Get report download logs"""
        
        query = select(ReportDownloadLog).options(
            selectinload(ReportDownloadLog.admin)
        )
        
        if admin_id:
            query = query.where(ReportDownloadLog.admin_id == admin_id)
        
        if report_type:
            query = query.where(ReportDownloadLog.report_type == report_type)
        
        query = query.offset(skip).limit(limit).order_by(ReportDownloadLog.downloaded_at.desc())
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [ReportDownloadLogResponse.model_validate(log) for log in logs]