"""
Notifications API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Dict, Any
from sqlalchemy import select

from ...core.database import get_db
from ...core.exceptions import EmailError
from ...models.schemas import MessageResponse
from ...models.db_models import User, UserRole
from ...services.auth_service import AuthService
from ...services.email_service import EmailService

router = APIRouter()


@router.post("/test", response_model=MessageResponse)
async def send_test_notification(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Send test notification"""
    # Only admins can send test notifications
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        email_service = EmailService()
        
        # Get current user
        user_result = await db.execute(select(User).where(User.id == current_user["user_id"]))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Send test email
        html_content = """
        <html>
        <body>
            <h2>테스트 알림</h2>
            <p>안녕하세요,</p>
            <p>이것은 GA4 Admin 시스템에서 발송된 테스트 이메일입니다.</p>
            <p>이메일 알림 시스템이 정상적으로 작동하고 있습니다.</p>
            <p>감사합니다.</p>
            <p>GA4 Admin System</p>
        </body>
        </html>
        """
        
        await email_service._send_email(
            to_email=user.email,
            subject="[GA4 Admin] 테스트 알림",
            html_content=html_content
        )
        
        return MessageResponse(message="Test notification sent successfully")
        
    except EmailError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send test notification: {e.message}"
        )


@router.post("/daily-summary", response_model=MessageResponse)
async def send_daily_summary(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Send daily summary email to all admins"""
    # Only super admins can trigger daily summary
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        email_service = EmailService()
        
        # Get all admin emails
        admin_result = await db.execute(
            select(User.email).where(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
        )
        admin_emails = [row[0] for row in admin_result.fetchall()]
        
        if not admin_emails:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No admin users found"
            )
        
        # Create summary data (simplified for now)
        summary_data = {
            "new_requests": 0,
            "approved_requests": 0,
            "rejected_requests": 0,
            "pending_requests": 0,
            "expiring_7days": 0,
            "expiring_30days": 0,
            "total_activities": 0,
            "active_users": len(admin_emails)
        }
        
        # Send daily summary
        success = await email_service.send_daily_summary_email(admin_emails, summary_data)
        
        if success:
            return MessageResponse(message="Daily summary sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to send daily summary to some recipients"
            )
        
    except EmailError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send daily summary: {e.message}"
        )


@router.get("/settings")
async def get_notification_settings(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> Dict[str, Any]:
    """Get notification settings"""
    # Only admins can view notification settings
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    from ...core.config import settings
    
    return {
        "email_notifications_enabled": settings.ENABLE_EMAIL_NOTIFICATIONS,
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_tls": settings.SMTP_TLS,
        "from_email": settings.EMAIL_FROM,
        "from_name": settings.EMAIL_FROM_NAME
    }