"""
Email notification service
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import aiosmtplib
from jinja2 import Environment, DictLoader

from ..core.config import settings
from ..core.exceptions import EmailError
from ..models.db_models import User, PermissionGrant, PermissionLevel, PermissionStatus

logger = logging.getLogger(__name__)

# Email templates
EMAIL_TEMPLATES = {
    "permission_request": """
<html>
<body>
    <h2>새로운 GA4 권한 요청</h2>
    <p>안녕하세요,</p>
    <p><strong>{{ requester_name }}</strong>님이 GA4 권한을 요청했습니다.</p>
    
    <h3>요청 세부사항:</h3>
    <ul>
        <li><strong>대상 이메일:</strong> {{ target_email }}</li>
        <li><strong>GA4 속성 ID:</strong> {{ property_id }}</li>
        <li><strong>권한 레벨:</strong> {{ permission_level }}</li>
        <li><strong>만료일:</strong> {{ expires_at }}</li>
        {% if reason %}
        <li><strong>요청 사유:</strong> {{ reason }}</li>
        {% endif %}
    </ul>
    
    <p>
        <a href="{{ approval_url }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">승인하기</a>
        <a href="{{ rejection_url }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-left: 10px;">거절하기</a>
    </p>
    
    <p>감사합니다.</p>
    <p>GA4 Admin System</p>
</body>
</html>
    """,
    
    "permission_approved": """
<html>
<body>
    <h2>GA4 권한 승인 완료</h2>
    <p>안녕하세요,</p>
    <p>요청하신 GA4 권한이 승인되었습니다.</p>
    
    <h3>승인된 권한:</h3>
    <ul>
        <li><strong>대상 이메일:</strong> {{ target_email }}</li>
        <li><strong>GA4 속성 ID:</strong> {{ property_id }}</li>
        <li><strong>권한 레벨:</strong> {{ permission_level }}</li>
        <li><strong>만료일:</strong> {{ expires_at }}</li>
        <li><strong>승인자:</strong> {{ approver_name }}</li>
        {% if notes %}
        <li><strong>승인 메모:</strong> {{ notes }}</li>
        {% endif %}
    </ul>
    
    <p>이제 해당 GA4 속성에 접근하실 수 있습니다.</p>
    
    <p>감사합니다.</p>
    <p>GA4 Admin System</p>
</body>
</html>
    """,
    
    "permission_rejected": """
<html>
<body>
    <h2>GA4 권한 요청 거절</h2>
    <p>안녕하세요,</p>
    <p>요청하신 GA4 권한이 거절되었습니다.</p>
    
    <h3>거절된 요청:</h3>
    <ul>
        <li><strong>대상 이메일:</strong> {{ target_email }}</li>
        <li><strong>GA4 속성 ID:</strong> {{ property_id }}</li>
        <li><strong>권한 레벨:</strong> {{ permission_level }}</li>
        <li><strong>거절자:</strong> {{ rejector_name }}</li>
        {% if reason %}
        <li><strong>거절 사유:</strong> {{ reason }}</li>
        {% endif %}
    </ul>
    
    <p>추가 문의사항이 있으시면 관리자에게 연락주세요.</p>
    
    <p>감사합니다.</p>
    <p>GA4 Admin System</p>
</body>
</html>
    """,
    
    "permission_expiry_warning": """
<html>
<body>
    <h2>GA4 권한 만료 안내</h2>
    <p>안녕하세요,</p>
    <p>보유하신 GA4 권한이 곧 만료됩니다.</p>
    
    <h3>만료 예정 권한:</h3>
    <ul>
        <li><strong>대상 이메일:</strong> {{ target_email }}</li>
        <li><strong>GA4 속성 ID:</strong> {{ property_id }}</li>
        <li><strong>권한 레벨:</strong> {{ permission_level }}</li>
        <li><strong>만료일:</strong> {{ expires_at }}</li>
        <li><strong>남은 기간:</strong> {{ days_remaining }}일</li>
    </ul>
    
    {% if permission_level in ['viewer', 'analyst'] %}
    <p>
        <a href="{{ extension_url }}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">권한 연장하기</a>
    </p>
    <p>위 버튼을 클릭하여 권한을 자동으로 연장할 수 있습니다.</p>
    {% else %}
    <p>권한 연장을 원하시면 관리자에게 연락주세요.</p>
    {% endif %}
    
    <p>감사합니다.</p>
    <p>GA4 Admin System</p>
</body>
</html>
    """,
    
    "permission_revoked": """
<html>
<body>
    <h2>GA4 권한 해제 안내</h2>
    <p>안녕하세요,</p>
    <p>보유하신 GA4 권한이 해제되었습니다.</p>
    
    <h3>해제된 권한:</h3>
    <ul>
        <li><strong>대상 이메일:</strong> {{ target_email }}</li>
        <li><strong>GA4 속성 ID:</strong> {{ property_id }}</li>
        <li><strong>권한 레벨:</strong> {{ permission_level }}</li>
        <li><strong>해제자:</strong> {{ revoker_name }}</li>
        {% if reason %}
        <li><strong>해제 사유:</strong> {{ reason }}</li>
        {% endif %}
    </ul>
    
    <p>해당 GA4 속성에 더 이상 접근하실 수 없습니다.</p>
    
    <p>감사합니다.</p>
    <p>GA4 Admin System</p>
</body>
</html>
    """,
    
    "password_reset": """
<html>
<body>
    <h2>비밀번호 재설정</h2>
    <p>안녕하세요,</p>
    <p>비밀번호 재설정 요청이 접수되었습니다.</p>
    
    <p>아래 링크를 클릭하여 새 비밀번호를 설정하세요:</p>
    <p>
        <a href="{{ reset_url }}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">비밀번호 재설정</a>
    </p>
    
    <p><strong>중요:</strong> 이 링크는 {{ expiry_minutes }}분 후에 만료됩니다.</p>
    
    <p>만약 비밀번호 재설정을 요청하지 않으셨다면 이 이메일을 무시하세요.</p>
    
    <p>감사합니다.</p>
    <p>GA4 Admin System</p>
</body>
</html>
    """
}


class EmailService:
    """Email notification service"""
    
    def __init__(self):
        self.template_env = Environment(loader=DictLoader(EMAIL_TEMPLATES))
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.smtp_ssl = settings.SMTP_SSL
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using aiosmtplib"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            if settings.ENABLE_EMAIL_NOTIFICATIONS:
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    use_tls=self.smtp_tls,
                    start_tls=True if self.smtp_tls else False
                )
                logger.info(f"Email sent successfully to {to_email}")
            else:
                logger.info(f"Email notifications disabled. Would send to {to_email}: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise EmailError(f"Failed to send email: {e}")
    
    async def send_permission_request_notification(
        self,
        grant: PermissionGrant,
        requester: User,
        admin_emails: List[str]
    ) -> bool:
        """Send notification about new permission request"""
        template = self.template_env.get_template("permission_request")
        
        context = {
            "requester_name": requester.name,
            "target_email": grant.target_email,
            "property_id": grant.ga_property_id,
            "permission_level": grant.permission_level.value,
            "expires_at": grant.expires_at.strftime("%Y-%m-%d") if grant.expires_at else "설정되지 않음",
            "reason": grant.reason,
            "approval_url": f"{settings.FRONTEND_URL}/dashboard/permissions/{grant.id}/approve",
            "rejection_url": f"{settings.FRONTEND_URL}/dashboard/permissions/{grant.id}/reject"
        }
        
        html_content = template.render(**context)
        subject = f"[GA4 Admin] 새로운 권한 요청 - {grant.target_email}"
        
        # Send to all admin emails
        success = True
        for admin_email in admin_emails:
            try:
                await self._send_email(admin_email, subject, html_content)
            except EmailError:
                success = False
        
        return success
    
    async def send_permission_approved_notification(
        self,
        grant: PermissionGrant,
        requester: User,
        approver: User
    ) -> bool:
        """Send notification about approved permission"""
        template = self.template_env.get_template("permission_approved")
        
        context = {
            "target_email": grant.target_email,
            "property_id": grant.ga_property_id,
            "permission_level": grant.permission_level.value,
            "expires_at": grant.expires_at.strftime("%Y-%m-%d") if grant.expires_at else "설정되지 않음",
            "approver_name": approver.name,
            "notes": grant.notes
        }
        
        html_content = template.render(**context)
        subject = f"[GA4 Admin] 권한 승인 완료 - {grant.target_email}"
        
        return await self._send_email(requester.email, subject, html_content)
    
    async def send_permission_rejected_notification(
        self,
        grant: PermissionGrant,
        requester: User,
        rejector: User,
        reason: Optional[str] = None
    ) -> bool:
        """Send notification about rejected permission"""
        template = self.template_env.get_template("permission_rejected")
        
        context = {
            "target_email": grant.target_email,
            "property_id": grant.ga_property_id,
            "permission_level": grant.permission_level.value,
            "rejector_name": rejector.name,
            "reason": reason or grant.notes
        }
        
        html_content = template.render(**context)
        subject = f"[GA4 Admin] 권한 요청 거절 - {grant.target_email}"
        
        return await self._send_email(requester.email, subject, html_content)
    
    async def send_permission_expiry_warning(
        self,
        grant: PermissionGrant,
        user: User,
        days_remaining: int
    ) -> bool:
        """Send warning about expiring permission"""
        template = self.template_env.get_template("permission_expiry_warning")
        
        context = {
            "target_email": grant.target_email,
            "property_id": grant.ga_property_id,
            "permission_level": grant.permission_level.value,
            "expires_at": grant.expires_at.strftime("%Y-%m-%d") if grant.expires_at else "설정되지 않음",
            "days_remaining": days_remaining,
            "extension_url": f"{settings.FRONTEND_URL}/extend/{grant.id}"
        }
        
        html_content = template.render(**context)
        subject = f"[GA4 Admin] 권한 만료 안내 ({days_remaining}일 남음) - {grant.target_email}"
        
        return await self._send_email(user.email, subject, html_content)
    
    async def send_permission_revoked_notification(
        self,
        grant: PermissionGrant,
        user: User,
        revoker: User,
        reason: Optional[str] = None
    ) -> bool:
        """Send notification about revoked permission"""
        template = self.template_env.get_template("permission_revoked")
        
        context = {
            "target_email": grant.target_email,
            "property_id": grant.ga_property_id,
            "permission_level": grant.permission_level.value,
            "revoker_name": revoker.name,
            "reason": reason
        }
        
        html_content = template.render(**context)
        subject = f"[GA4 Admin] 권한 해제 안내 - {grant.target_email}"
        
        return await self._send_email(user.email, subject, html_content)
    
    async def send_password_reset_email(
        self,
        user: User,
        reset_token: str
    ) -> bool:
        """Send password reset email"""
        template = self.template_env.get_template("password_reset")
        
        context = {
            "reset_url": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
            "expiry_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        }
        
        html_content = template.render(**context)
        subject = "[GA4 Admin] 비밀번호 재설정"
        
        return await self._send_email(user.email, subject, html_content)
    
    async def send_daily_summary_email(
        self,
        admin_emails: List[str],
        summary_data: Dict[str, Any]
    ) -> bool:
        """Send daily summary email to admins"""
        # Create daily summary HTML
        html_content = f"""
        <html>
        <body>
            <h2>GA4 Admin 일일 요약 리포트</h2>
            <p>안녕하세요,</p>
            <p>{datetime.now().strftime('%Y년 %m월 %d일')} 시스템 활동 요약입니다.</p>
            
            <h3>권한 요청 현황:</h3>
            <ul>
                <li>새로운 요청: {summary_data.get('new_requests', 0)}건</li>
                <li>승인된 요청: {summary_data.get('approved_requests', 0)}건</li>
                <li>거절된 요청: {summary_data.get('rejected_requests', 0)}건</li>
                <li>대기 중인 요청: {summary_data.get('pending_requests', 0)}건</li>
            </ul>
            
            <h3>권한 만료 알림:</h3>
            <ul>
                <li>7일 내 만료: {summary_data.get('expiring_7days', 0)}건</li>
                <li>30일 내 만료: {summary_data.get('expiring_30days', 0)}건</li>
            </ul>
            
            <h3>시스템 활동:</h3>
            <ul>
                <li>총 활동 수: {summary_data.get('total_activities', 0)}건</li>
                <li>활성 사용자: {summary_data.get('active_users', 0)}명</li>
            </ul>
            
            <p>
                <a href="{settings.FRONTEND_URL}/dashboard" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">대시보드 보기</a>
            </p>
            
            <p>감사합니다.</p>
            <p>GA4 Admin System</p>
        </body>
        </html>
        """
        
        subject = f"[GA4 Admin] 일일 요약 리포트 - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Send to all admin emails
        success = True
        for admin_email in admin_emails:
            try:
                await self._send_email(admin_email, subject, html_content)
            except EmailError:
                success = False
        
        return success