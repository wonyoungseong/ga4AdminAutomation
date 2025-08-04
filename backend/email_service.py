#!/usr/bin/env python3
"""
Email notification service for GA4 Admin Automation System
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # SMTP 설정 (환경변수 또는 기본값)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'GA4 관리 시스템')
        
        # 이메일 활성화 여부
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        
        if not self.email_enabled:
            logger.info("이메일 서비스가 비활성화되어 있습니다.")
        elif not all([self.smtp_username, self.smtp_password]):
            logger.warning("이메일 인증 정보가 설정되지 않았습니다.")
            self.email_enabled = False

    def send_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        is_html: bool = True,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> bool:
        """이메일 전송"""
        if not self.email_enabled:
            logger.info(f"이메일 전송 시뮬레이션: {to_emails} - {subject}")
            return True
            
        try:
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 본문 첨부
            if is_html:
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP 연결 및 전송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # 수신자 목록 구성
                recipients = to_emails.copy()
                if cc_emails:
                    recipients.extend(cc_emails)
                if bcc_emails:
                    recipients.extend(bcc_emails)
                
                server.send_message(msg, to_addrs=recipients)
                
            logger.info(f"이메일 전송 성공: {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 전송 실패: {str(e)}")
            return False

    def send_permission_request_notification(
        self, 
        requester_email: str, 
        requester_name: str, 
        client_name: str, 
        properties: List[dict],
        admin_emails: List[str]
    ) -> bool:
        """권한 요청 알림 전송 (관리자에게)"""
        
        subject = f"[GA4 관리 시스템] 새로운 권한 요청 - {client_name}"
        
        # HTML 이메일 템플릿
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4285f4; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
                .property {{ background-color: white; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #4285f4; }}
                .button {{ display: inline-block; background-color: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔔 새로운 GA4 권한 요청</h2>
                </div>
                <div class="content">
                    <p><strong>요청자:</strong> {requester_name} ({requester_email})</p>
                    <p><strong>클라이언트:</strong> {client_name}</p>
                    <p><strong>요청 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h3>📊 요청된 GA4 Property 권한:</h3>
        """
        
        for prop in properties:
            html_body += f"""
                    <div class="property">
                        <strong>{prop.get('property_name', 'N/A')}</strong><br>
                        Property ID: {prop.get('property_id', 'N/A')}<br>
                        현재 권한: {prop.get('current_permission', 'None')}<br>
                        요청 권한: <strong>{prop.get('requested_permission', 'N/A')}</strong>
                    </div>
            """
        
        html_body += f"""
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/dashboard/permissions" class="button">권한 요청 검토하기</a>
                    </div>
                    
                    <p>관리자 대시보드에서 해당 요청을 승인하거나 거부할 수 있습니다.</p>
                </div>
                <div class="footer">
                    <p>이 메일은 GA4 관리 시스템에서 자동으로 발송되었습니다.</p>
                    <p>문의사항이 있으시면 시스템 관리자에게 연락하세요.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(admin_emails, subject, html_body)

    def send_permission_approved_notification(
        self, 
        requester_email: str, 
        requester_name: str, 
        client_name: str, 
        properties: List[dict],
        approved_by: str
    ) -> bool:
        """권한 승인 알림 전송 (요청자에게)"""
        
        subject = f"[GA4 관리 시스템] 권한 요청 승인됨 - {client_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #34a853; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
                .property {{ background-color: white; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #34a853; }}
                .button {{ display: inline-block; background-color: #34a853; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ GA4 권한 요청이 승인되었습니다</h2>
                </div>
                <div class="content">
                    <p>안녕하세요 {requester_name}님,</p>
                    <p><strong>클라이언트:</strong> {client_name}</p>
                    <p><strong>승인자:</strong> {approved_by}</p>
                    <p><strong>승인 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h3>📊 승인된 GA4 Property 권한:</h3>
        """
        
        for prop in properties:
            html_body += f"""
                    <div class="property">
                        <strong>{prop.get('property_name', 'N/A')}</strong><br>
                        Property ID: {prop.get('property_id', 'N/A')}<br>
                        부여된 권한: <strong>{prop.get('requested_permission', 'N/A')}</strong>
                    </div>
            """
        
        html_body += f"""
                    <p>이제 Google Analytics 4에서 해당 Property들에 접근할 수 있습니다.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://analytics.google.com" class="button">Google Analytics 4 바로가기</a>
                    </div>
                </div>
                <div class="footer">
                    <p>이 메일은 GA4 관리 시스템에서 자동으로 발송되었습니다.</p>
                    <p>문의사항이 있으시면 시스템 관리자에게 연락하세요.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([requester_email], subject, html_body)

    def send_permission_rejected_notification(
        self, 
        requester_email: str, 
        requester_name: str, 
        client_name: str, 
        properties: List[dict],
        rejected_by: str,
        reason: str = ""
    ) -> bool:
        """권한 거부 알림 전송 (요청자에게)"""
        
        subject = f"[GA4 관리 시스템] 권한 요청 거부됨 - {client_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ea4335; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
                .property {{ background-color: white; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #ea4335; }}
                .reason {{ background-color: #fef7e6; padding: 15px; border-radius: 5px; border-left: 4px solid #fbbc04; margin: 15px 0; }}
                .button {{ display: inline-block; background-color: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ GA4 권한 요청이 거부되었습니다</h2>
                </div>
                <div class="content">
                    <p>안녕하세요 {requester_name}님,</p>
                    <p><strong>클라이언트:</strong> {client_name}</p>
                    <p><strong>거부자:</strong> {rejected_by}</p>
                    <p><strong>거부 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h3>📊 거부된 GA4 Property 권한:</h3>
        """
        
        for prop in properties:
            html_body += f"""
                    <div class="property">
                        <strong>{prop.get('property_name', 'N/A')}</strong><br>
                        Property ID: {prop.get('property_id', 'N/A')}<br>
                        요청했던 권한: {prop.get('requested_permission', 'N/A')}
                    </div>
            """
        
        if reason:
            html_body += f"""
                    <div class="reason">
                        <strong>거부 사유:</strong><br>
                        {reason}
                    </div>
            """
        
        html_body += f"""
                    <p>필요시 추가 정보를 제공하여 다시 요청하실 수 있습니다.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/dashboard/permissions" class="button">새 권한 요청하기</a>
                    </div>
                </div>
                <div class="footer">
                    <p>이 메일은 GA4 관리 시스템에서 자동으로 발송되었습니다.</p>
                    <p>문의사항이 있으시면 시스템 관리자에게 연락하세요.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([requester_email], subject, html_body)

# 전역 이메일 서비스 인스턴스
email_service = EmailService()