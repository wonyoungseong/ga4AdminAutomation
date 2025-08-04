"""
Background scheduler service - Legacy compatible
Handles periodic tasks like permission expiry checks, notifications, and sync operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..core.database import get_async_session
from ..models.db_models import (
    UserPermission, PermissionGrant, GA4Property, User,
    PermissionStatus, NotificationStatus, NotificationLog
)
from ..services.notification_service import NotificationService
from ..services.ga4_property_service import GA4PropertyService
from ..services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background scheduler service - Legacy compatible"""
    
    def __init__(self):
        self.is_running = False
        self._tasks = {}
    
    async def start(self):
        """Start the scheduler service"""
        if self.is_running:
            logger.warning("Scheduler service is already running")
            return
        
        self.is_running = True
        logger.info("Starting scheduler service")
        
        # Start background tasks
        self._tasks['expired_permissions'] = asyncio.create_task(
            self._run_expired_permissions_check()
        )
        self._tasks['expiry_notifications'] = asyncio.create_task(
            self._run_expiry_notifications_check()
        )
        self._tasks['property_sync'] = asyncio.create_task(
            self._run_property_sync_check()
        )
        self._tasks['notification_retry'] = asyncio.create_task(
            self._run_notification_retry_check()
        )
        self._tasks['cleanup'] = asyncio.create_task(
            self._run_cleanup_tasks()
        )
        
        logger.info("Scheduler service started successfully")
    
    async def stop(self):
        """Stop the scheduler service"""
        if not self.is_running:
            logger.warning("Scheduler service is not running")
            return
        
        self.is_running = False
        logger.info("Stopping scheduler service")
        
        # Cancel all tasks
        for task_name, task in self._tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled scheduler task: {task_name}")
        
        self._tasks.clear()
        logger.info("Scheduler service stopped")
    
    async def _run_expired_permissions_check(self):
        """Periodically check and handle expired permissions"""
        while self.is_running:
            try:
                async with get_async_session() as db:
                    result = await self._check_expired_permissions(db)
                    if result['expired_count'] > 0:
                        logger.info(f"Processed {result['expired_count']} expired permissions")
                
            except Exception as e:
                logger.error(f"Error in expired permissions check: {e}")
            
            # Run every hour
            await asyncio.sleep(3600)
    
    async def _run_expiry_notifications_check(self):
        """Periodically send expiry notifications"""
        while self.is_running:
            try:
                async with get_async_session() as db:
                    result = await self._send_expiry_notifications(db)
                    if result['notification_count'] > 0:
                        logger.info(f"Sent {result['notification_count']} expiry notifications")
                
            except Exception as e:
                logger.error(f"Error in expiry notifications check: {e}")
            
            # Run every 6 hours
            await asyncio.sleep(21600)
    
    async def _run_property_sync_check(self):
        """Periodically sync GA4 properties"""
        while self.is_running:
            try:
                async with get_async_session() as db:
                    result = await self._sync_ga4_properties(db)
                    if result['sync_count'] > 0:
                        logger.info(f"Synced {result['sync_count']} GA4 properties")
                
            except Exception as e:
                logger.error(f"Error in property sync check: {e}")
            
            # Run every 24 hours
            await asyncio.sleep(86400)
    
    async def _run_notification_retry_check(self):
        """Periodically retry failed notifications"""
        while self.is_running:
            try:
                async with get_async_session() as db:
                    notification_service = NotificationService(db)
                    result = await notification_service.retry_failed_notifications()
                    if result['retry_count'] > 0:
                        logger.info(f"Retried {result['retry_count']} failed notifications")
                
            except Exception as e:
                logger.error(f"Error in notification retry check: {e}")
            
            # Run every 30 minutes
            await asyncio.sleep(1800)
    
    async def _run_cleanup_tasks(self):
        """Periodically run cleanup tasks"""
        while self.is_running:
            try:
                async with get_async_session() as db:
                    result = await self._cleanup_old_data(db)
                    if result['cleaned_records'] > 0:
                        logger.info(f"Cleaned up {result['cleaned_records']} old records")
                
            except Exception as e:
                logger.error(f"Error in cleanup tasks: {e}")
            
            # Run every 24 hours
            await asyncio.sleep(86400)
    
    async def _check_expired_permissions(self, db: AsyncSession) -> Dict[str, Any]:
        """Check and handle expired permissions"""
        
        # Find expired user permissions
        user_permissions_result = await db.execute(
            select(UserPermission)
            .options(
                selectinload(UserPermission.user),
                selectinload(UserPermission.ga_property)
            )
            .where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_user_permissions = user_permissions_result.scalars().all()
        
        # Find expired permission grants
        permission_grants_result = await db.execute(
            select(PermissionGrant)
            .options(
                selectinload(PermissionGrant.user),
                selectinload(PermissionGrant.client)
            )
            .where(
                and_(
                    PermissionGrant.status == PermissionStatus.APPROVED,
                    PermissionGrant.expires_at.is_not(None),
                    PermissionGrant.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_permission_grants = permission_grants_result.scalars().all()
        
        expired_count = 0
        
        # Process expired user permissions
        for permission in expired_user_permissions:
            permission.status = PermissionStatus.EXPIRED
            expired_count += 1
            
            # Log the expiration
            audit_service = AuditService(db)
            await audit_service.log_action(
                actor_id=None,  # System action
                action="expire_user_permission",
                resource_type="user_permission",
                resource_id=str(permission.id),
                details=f"User permission for {permission.target_email} expired automatically"
            )
        
        # Process expired permission grants
        for grant in expired_permission_grants:
            grant.status = PermissionStatus.EXPIRED
            expired_count += 1
            
            # Log the expiration
            audit_service = AuditService(db)
            await audit_service.log_action(
                actor_id=None,  # System action
                action="expire_permission_grant",
                resource_type="permission_grant",
                resource_id=str(grant.id),
                details=f"Permission grant for {grant.target_email} expired automatically"
            )
        
        await db.commit()
        
        return {
            "expired_count": expired_count,
            "user_permissions": len(expired_user_permissions),
            "permission_grants": len(expired_permission_grants),
            "checked_at": datetime.utcnow()
        }
    
    async def _send_expiry_notifications(self, db: AsyncSession) -> Dict[str, Any]:
        """Send notifications for permissions expiring soon"""
        
        notification_service = NotificationService(db)
        notification_count = 0
        
        # Find user permissions expiring in 7 days
        expiring_threshold = datetime.utcnow() + timedelta(days=7)
        
        user_permissions_result = await db.execute(
            select(UserPermission)
            .options(
                selectinload(UserPermission.user),
                selectinload(UserPermission.ga_property)
            )
            .where(
                and_(
                    UserPermission.status == PermissionStatus.APPROVED,
                    UserPermission.expires_at <= expiring_threshold,
                    UserPermission.expires_at > datetime.utcnow()
                )
            )
        )
        expiring_user_permissions = user_permissions_result.scalars().all()
        
        # Send notifications for expiring user permissions
        for permission in expiring_user_permissions:
            # Check if we already sent a notification recently (within 24 hours)
            recent_notification_result = await db.execute(
                select(NotificationLog)
                .where(
                    and_(
                        NotificationLog.recipient == permission.target_email,
                        NotificationLog.template_type == "permission_expiry",
                        NotificationLog.created_at > (datetime.utcnow() - timedelta(hours=24))
                    )
                )
            )
            recent_notification = recent_notification_result.scalar_one_or_none()
            
            if recent_notification:
                continue  # Skip if already notified recently
            
            try:
                await notification_service.send_permission_expiry_notification(
                    recipient_email=permission.target_email,
                    user_name=permission.user.name,
                    property_name=permission.ga_property.property_name,
                    permission_level=permission.permission_level.value,
                    expires_at=permission.expires_at,
                    days_until_expiry=permission.days_until_expiry
                )
                notification_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send expiry notification for permission {permission.id}: {e}")
        
        # Find permission grants expiring in 7 days
        permission_grants_result = await db.execute(
            select(PermissionGrant)
            .options(
                selectinload(PermissionGrant.user),
                selectinload(PermissionGrant.client)
            )
            .where(
                and_(
                    PermissionGrant.status == PermissionStatus.APPROVED,
                    PermissionGrant.expires_at.is_not(None),
                    PermissionGrant.expires_at <= expiring_threshold,
                    PermissionGrant.expires_at > datetime.utcnow()
                )
            )
        )
        expiring_permission_grants = permission_grants_result.scalars().all()
        
        # Send notifications for expiring permission grants
        for grant in expiring_permission_grants:
            # Check if we already sent a notification recently (within 24 hours)
            recent_notification_result = await db.execute(
                select(NotificationLog)
                .where(
                    and_(
                        NotificationLog.recipient == grant.target_email,
                        NotificationLog.template_type == "permission_expiry",
                        NotificationLog.created_at > (datetime.utcnow() - timedelta(hours=24))
                    )
                )
            )
            recent_notification = recent_notification_result.scalar_one_or_none()
            
            if recent_notification:
                continue  # Skip if already notified recently
            
            try:
                days_until_expiry = (grant.expires_at - datetime.utcnow()).days
                await notification_service.send_permission_expiry_notification(
                    recipient_email=grant.target_email,
                    user_name=grant.user.name,
                    property_name=f"{grant.client.name} - {grant.ga_property_id}",
                    permission_level=grant.permission_level.value,
                    expires_at=grant.expires_at,
                    days_until_expiry=days_until_expiry
                )
                notification_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send expiry notification for grant {grant.id}: {e}")
        
        return {
            "notification_count": notification_count,
            "user_permissions": len(expiring_user_permissions),
            "permission_grants": len(expiring_permission_grants),
            "checked_at": datetime.utcnow()
        }
    
    async def _sync_ga4_properties(self, db: AsyncSession) -> Dict[str, Any]:
        """Sync GA4 properties that need updates"""
        
        ga4_service = GA4PropertyService(db)
        
        # Get properties that need sync
        properties_needing_sync = await ga4_service.get_properties_needing_sync()
        
        sync_count = 0
        for property_response in properties_needing_sync:
            try:
                # Use system user ID (0) for scheduled syncs
                await ga4_service.sync_property(property_response.id, user_id=0)
                sync_count += 1
                
            except Exception as e:
                logger.error(f"Failed to sync property {property_response.id}: {e}")
        
        return {
            "sync_count": sync_count,
            "total_properties": len(properties_needing_sync),
            "synced_at": datetime.utcnow()
        }
    
    async def _cleanup_old_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Clean up old data that's no longer needed"""
        
        cleaned_records = 0
        
        # Clean up old notification logs (older than 90 days)
        old_notifications_result = await db.execute(
            select(NotificationLog)
            .where(
                and_(
                    NotificationLog.created_at < (datetime.utcnow() - timedelta(days=90)),
                    NotificationLog.status.in_([NotificationStatus.SENT, NotificationStatus.FAILED])
                )
            )
        )
        old_notifications = old_notifications_result.scalars().all()
        
        for notification in old_notifications:
            await db.delete(notification)
            cleaned_records += 1
        
        # Clean up old audit logs (older than 1 year) - keep system actions
        # TODO: Implement when audit log retention policy is defined
        
        await db.commit()
        
        return {
            "cleaned_records": cleaned_records,
            "cleaned_at": datetime.utcnow()
        }
    
    async def run_manual_task(self, task_name: str) -> Dict[str, Any]:
        """Run a scheduled task manually"""
        
        async with get_async_session() as db:
            if task_name == "expired_permissions":
                return await self._check_expired_permissions(db)
            
            elif task_name == "expiry_notifications":
                return await self._send_expiry_notifications(db)
            
            elif task_name == "property_sync":
                return await self._sync_ga4_properties(db)
            
            elif task_name == "notification_retry":
                notification_service = NotificationService(db)
                return await notification_service.retry_failed_notifications()
            
            elif task_name == "cleanup":
                return await self._cleanup_old_data(db)
            
            else:
                raise ValueError(f"Unknown task: {task_name}")
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler service status"""
        
        task_status = {}
        for task_name, task in self._tasks.items():
            task_status[task_name] = {
                "running": not task.done(),
                "cancelled": task.cancelled() if task.done() else False,
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return {
            "is_running": self.is_running,
            "tasks": task_status,
            "status_checked_at": datetime.utcnow()
        }


# Global scheduler instance
scheduler = SchedulerService()