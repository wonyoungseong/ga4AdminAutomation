"""
Notification service - Legacy compatible
Handles email and other notification channels
"""

import json
import smtplib
from datetime import datetime
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..core.exceptions import NotFoundError, ValidationError
from ..models.db_models import (
    NotificationLog, AuditLog, User,
    NotificationChannel, NotificationStatus
)
from ..models.schemas import NotificationLogResponse
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Notification service - Legacy compatible"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def send_email_notification(
        self,
        recipient: str,
        subject: str,
        message_body: str,
        template_type: str,
        template_data: Optional[Dict[str, Any]] = None,
        audit_log_id: Optional[int] = None
    ) -> NotificationLogResponse:
        """Send email notification"""
        
        # Create notification log entry
        notification_log = NotificationLog(
            audit_log_id=audit_log_id,
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            template_type=template_type,
            subject=subject,
            message_body=message_body,
            template_data=json.dumps(template_data) if template_data else None,
            status=NotificationStatus.PENDING
        )
        
        self.db.add(notification_log)
        await self.db.commit()
        await self.db.refresh(notification_log)
        
        try:
            # Send the actual email
            await self._send_email(recipient, subject, message_body)
            
            # Update status to sent
            notification_log.status = NotificationStatus.SENT
            notification_log.sent_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Successfully sent email to {recipient}")
            
        except Exception as e:
            # Update status to failed
            notification_log.status = NotificationStatus.FAILED
            notification_log.error_message = str(e)
            notification_log.retry_count += 1
            
            await self.db.commit()
            
            logger.error(f"Failed to send email to {recipient}: {e}")
            
            # If retry count is less than 3, mark for retry
            if notification_log.retry_count < 3:
                notification_log.status = NotificationStatus.RETRYING
                await self.db.commit()
        
        return NotificationLogResponse.model_validate(notification_log)
    
    async def _send_email(self, recipient: str, subject: str, message_body: str):
        """Send actual email using SMTP"""
        
        if not settings.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email send")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = recipient
            
            # Add HTML body
            html_part = MIMEText(message_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    async def send_permission_request_notification(
        self,
        admin_email: str,
        requester_name: str,
        requester_email: str,
        client_name: str,
        property_name: str,
        permission_level: str,
        justification: str,
        audit_log_id: Optional[int] = None
    ) -> NotificationLogResponse:
        """Send permission request notification to admin"""
        
        subject = f"GA4 Permission Request - {requester_name}"
        
        message_body = f"""
        <html>
        <body>
            <h2>New GA4 Permission Request</h2>
            <p>A new permission request has been submitted and requires your approval.</p>
            
            <h3>Request Details:</h3>
            <ul>
                <li><strong>Requester:</strong> {requester_name} ({requester_email})</li>
                <li><strong>Client:</strong> {client_name}</li>
                <li><strong>Property:</strong> {property_name}</li>
                <li><strong>Permission Level:</strong> {permission_level}</li>
                <li><strong>Business Justification:</strong> {justification}</li>
                <li><strong>Submitted:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
            </ul>
            
            <p>Please review and approve/reject this request in the GA4 Admin Dashboard.</p>
            
            <p>Best regards,<br>GA4 Admin Automation System</p>
        </body>
        </html>
        """
        
        template_data = {
            "requester_name": requester_name,
            "requester_email": requester_email,
            "client_name": client_name,
            "property_name": property_name,
            "permission_level": permission_level,
            "justification": justification
        }
        
        return await self.send_email_notification(
            recipient=admin_email,
            subject=subject,
            message_body=message_body,
            template_type="permission_request",
            template_data=template_data,
            audit_log_id=audit_log_id
        )
    
    async def send_permission_approved_notification(
        self,
        recipient_email: str,
        requester_name: str,
        client_name: str,
        property_name: str,
        permission_level: str,
        expires_at: datetime,
        audit_log_id: Optional[int] = None
    ) -> NotificationLogResponse:
        """Send permission approved notification"""
        
        subject = f"GA4 Permission Approved - {property_name}"
        
        message_body = f"""
        <html>
        <body>
            <h2>GA4 Permission Approved</h2>
            <p>Your GA4 permission request has been approved!</p>
            
            <h3>Approved Permission:</h3>
            <ul>
                <li><strong>Client:</strong> {client_name}</li>
                <li><strong>Property:</strong> {property_name}</li>
                <li><strong>Permission Level:</strong> {permission_level}</li>
                <li><strong>Valid Until:</strong> {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if expires_at else 'No expiration'}</li>
            </ul>
            
            <p>You should now have access to the GA4 property. If you experience any issues, please contact your administrator.</p>
            
            <p>Best regards,<br>GA4 Admin Automation System</p>
        </body>
        </html>
        """
        
        template_data = {
            "requester_name": requester_name,
            "client_name": client_name,
            "property_name": property_name,
            "permission_level": permission_level,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
        
        return await self.send_email_notification(
            recipient=recipient_email,
            subject=subject,
            message_body=message_body,
            template_type="permission_approved",
            template_data=template_data,
            audit_log_id=audit_log_id
        )
    
    async def send_permission_rejected_notification(
        self,
        recipient_email: str,
        requester_name: str,
        client_name: str,
        property_name: str,
        permission_level: str,
        rejection_reason: str,
        audit_log_id: Optional[int] = None
    ) -> NotificationLogResponse:
        """Send permission rejected notification"""
        
        subject = f"GA4 Permission Rejected - {property_name}"
        
        message_body = f"""
        <html>
        <body>
            <h2>GA4 Permission Rejected</h2>
            <p>Unfortunately, your GA4 permission request has been rejected.</p>
            
            <h3>Rejected Request:</h3>
            <ul>
                <li><strong>Client:</strong> {client_name}</li>
                <li><strong>Property:</strong> {property_name}</li>
                <li><strong>Permission Level:</strong> {permission_level}</li>
                <li><strong>Rejection Reason:</strong> {rejection_reason}</li>
            </ul>
            
            <p>If you have questions about this decision, please contact your administrator.</p>
            
            <p>Best regards,<br>GA4 Admin Automation System</p>
        </body>
        </html>
        """
        
        template_data = {
            "requester_name": requester_name,
            "client_name": client_name,
            "property_name": property_name,
            "permission_level": permission_level,
            "rejection_reason": rejection_reason
        }
        
        return await self.send_email_notification(
            recipient=recipient_email,
            subject=subject,
            message_body=message_body,
            template_type="permission_rejected",
            template_data=template_data,
            audit_log_id=audit_log_id
        )
    
    async def send_permission_expiry_notification(
        self,
        recipient_email: str,
        user_name: str,
        property_name: str,
        permission_level: str,
        expires_at: datetime,
        days_until_expiry: int,
        audit_log_id: Optional[int] = None
    ) -> NotificationLogResponse:
        """Send permission expiry notification"""
        
        subject = f"GA4 Permission Expiring - {property_name} ({days_until_expiry} days)"
        
        message_body = f"""
        <html>
        <body>
            <h2>GA4 Permission Expiring Soon</h2>
            <p>Your GA4 permission is expiring soon and will need to be renewed.</p>
            
            <h3>Expiring Permission:</h3>
            <ul>
                <li><strong>Property:</strong> {property_name}</li>
                <li><strong>Permission Level:</strong> {permission_level}</li>
                <li><strong>Expires:</strong> {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                <li><strong>Days Remaining:</strong> {days_until_expiry}</li>
            </ul>
            
            <p>To maintain access, please submit a new permission request or contact your administrator for an extension.</p>
            
            <p>Best regards,<br>GA4 Admin Automation System</p>
        </body>
        </html>
        """
        
        template_data = {
            "user_name": user_name,
            "property_name": property_name,
            "permission_level": permission_level,
            "expires_at": expires_at.isoformat(),
            "days_until_expiry": days_until_expiry
        }
        
        return await self.send_email_notification(
            recipient=recipient_email,
            subject=subject,
            message_body=message_body,
            template_type="permission_expiry",
            template_data=template_data,
            audit_log_id=audit_log_id
        )
    
    async def send_permission_revoked_notification(
        self,
        recipient_email: str,
        user_name: str,
        property_name: str,
        permission_level: str,
        revocation_reason: str,
        audit_log_id: Optional[int] = None
    ) -> NotificationLogResponse:
        """Send permission revoked notification"""
        
        subject = f"GA4 Permission Revoked - {property_name}"
        
        message_body = f"""
        <html>
        <body>
            <h2>GA4 Permission Revoked</h2>
            <p>Your GA4 permission has been revoked.</p>
            
            <h3>Revoked Permission:</h3>
            <ul>
                <li><strong>Property:</strong> {property_name}</li>
                <li><strong>Permission Level:</strong> {permission_level}</li>
                <li><strong>Revocation Reason:</strong> {revocation_reason}</li>
                <li><strong>Revoked At:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
            </ul>
            
            <p>You no longer have access to this GA4 property. If you believe this is an error, please contact your administrator.</p>
            
            <p>Best regards,<br>GA4 Admin Automation System</p>
        </body>
        </html>
        """
        
        template_data = {
            "user_name": user_name,
            "property_name": property_name,
            "permission_level": permission_level,
            "revocation_reason": revocation_reason
        }
        
        return await self.send_email_notification(
            recipient=recipient_email,
            subject=subject,
            message_body=message_body,
            template_type="permission_revoked",
            template_data=template_data,
            audit_log_id=audit_log_id
        )
    
    async def retry_failed_notifications(self) -> Dict[str, Any]:
        """Retry failed notifications"""
        
        # Get notifications that need retry
        result = await self.db.execute(
            select(NotificationLog).where(
                NotificationLog.status == NotificationStatus.RETRYING
            ).limit(10)  # Process 10 at a time
        )
        notifications = result.scalars().all()
        
        retry_count = 0
        success_count = 0
        
        for notification in notifications:
            if notification.retry_count >= 3:
                # Mark as permanently failed
                notification.status = NotificationStatus.FAILED
                notification.error_message = "Max retry attempts reached"
                continue
            
            try:
                # Retry sending
                await self._send_email(
                    notification.recipient,
                    notification.subject or f"Notification - {notification.template_type}",
                    notification.message_body or "No message body"
                )
                
                # Mark as sent
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                success_count += 1
                
            except Exception as e:
                # Increment retry count
                notification.retry_count += 1
                notification.error_message = str(e)
                
                if notification.retry_count >= 3:
                    notification.status = NotificationStatus.FAILED
                
            retry_count += 1
        
        await self.db.commit()
        
        return {
            "retry_count": retry_count,
            "success_count": success_count,
            "failed_count": retry_count - success_count
        }
    
    async def get_notification_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        channel: Optional[NotificationChannel] = None,
        status: Optional[NotificationStatus] = None,
        template_type: Optional[str] = None
    ) -> List[NotificationLogResponse]:
        """Get notification logs with filters"""
        
        query = select(NotificationLog)
        
        if channel:
            query = query.where(NotificationLog.channel == channel)
        
        if status:
            query = query.where(NotificationLog.status == status)
        
        if template_type:
            query = query.where(NotificationLog.template_type == template_type)
        
        query = query.offset(skip).limit(limit).order_by(NotificationLog.created_at.desc())
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        return [NotificationLogResponse.model_validate(notif) for notif in notifications]
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        
        # Total notifications
        total_result = await self.db.execute(
            select(func.count(NotificationLog.id))
        )
        total = total_result.scalar()
        
        # By status
        status_result = await self.db.execute(
            select(
                NotificationLog.status,
                func.count(NotificationLog.id)
            ).group_by(NotificationLog.status)
        )
        status_counts = {status: count for status, count in status_result.fetchall()}
        
        # By channel
        channel_result = await self.db.execute(
            select(
                NotificationLog.channel,
                func.count(NotificationLog.id)
            ).group_by(NotificationLog.channel)
        )
        channel_counts = {channel: count for channel, count in channel_result.fetchall()}
        
        return {
            "total_notifications": total,
            "by_status": status_counts,
            "by_channel": channel_counts,
            "generated_at": datetime.utcnow()
        }