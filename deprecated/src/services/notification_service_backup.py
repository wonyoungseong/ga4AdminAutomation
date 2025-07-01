#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 알림 서비스
=======================

사용자 등록, 만료 알림, 삭제 알림 등 모든 이메일 알림을 처리하는 서비스
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from ..core.logger import get_ga4_logger
from ..core.gmail_service import GmailOAuthSender
from ..infrastructure.database import db_manager
from ..web.templates.email_templates import EmailTemplates


class NotificationType(Enum):
    """알림 타입"""
    WELCOME = "welcome"
    EXPIRY_WARNING_30 = "30_days"
    EXPIRY_WARNING_7 = "7_days"
    EXPIRY_WARNING_1 = "1_day"
    EXPIRY_TODAY = "today"
    DELETION_NOTICE = "expired"
    EDITOR_AUTO_DOWNGRADE = "editor_auto_downgrade"
    ADMIN_NOTIFICATION = "admin_notification"
    EXTENSION_APPROVED = "extension_approved"
    TEST = "test"


class NotificationService:
    """알림 서비스 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.gmail_sender = None
        self.config = self._load_config()
        self.db_manager = db_manager
        self.email_templates = EmailTemplates()
        
    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
            return {}
    
    async def initialize(self):
        """서비스 초기화"""
        try:
            self.gmail_sender = GmailOAuthSender()
            self.logger.info("✅ 알림 서비스 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ 알림 서비스 초기화 실패: {e}")
            raise
    
    async def send_welcome_email(self, user_email: str, property_name: str, 
                                property_id: str, role: str, expiry_date: Optional[datetime] = None) -> bool:
        """환영 이메일 발송"""
        try:
            subject = f"🎉 GA4 권한 부여 완료 - {property_name}"
            
            expiry_str = expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else "무제한"
            role_korean = self._get_role_korean(role)
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🎉 GA4 권한 부여 완료</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Google Analytics 4 접근 권한이 성공적으로 부여되었습니다</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #495057; margin-top: 0;">📊 권한 정보</h2>
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <tr style="background: white;">
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; width: 30%;">사용자</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{user_email}</td>
                            </tr>
                            <tr style="background: #f8f9fa;">
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">프로퍼티</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{property_name}</td>
                            </tr>
                            <tr style="background: white;">
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">권한 레벨</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{role_korean}</td>
                            </tr>
                            <tr style="background: #f8f9fa;">
                                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">만료일</td>
                                <td style="padding: 12px; border: 1px solid #dee2e6;">{expiry_str}</td>
                            </tr>
                        </table>
                        
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #1565c0;">🚀 시작하기</h3>
                            <p style="margin: 0 0 15px 0;">아래 링크를 클릭하여 Google Analytics에 접속하세요:</p>
                            <a href="https://analytics.google.com/analytics/web/#/p{property_id}/reports/intelligenthome" 
                               style="background: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                📈 GA4 접속하기
                            </a>
                        </div>
                        
                        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #e65100;">⚠️ 중요 안내</h3>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>권한은 <strong>{expiry_str}</strong>까지 유효합니다</li>
                                <li>만료 30일, 7일, 1일 전에 알림을 받게 됩니다</li>
                                <li>Editor 권한은 7일 후 자동으로 Viewer로 변경됩니다</li>
                                <li>권한 연장이 필요한 경우 관리자에게 문의하세요</li>
                            </ul>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                            이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
                            발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
GA4 권한 부여 완료

안녕하세요, {user_email}님!

Google Analytics 4 속성에 대한 접근 권한이 성공적으로 부여되었습니다.

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 권한 레벨: {role_korean}
- 만료일: {expiry_str}

GA4 접속: https://analytics.google.com/analytics/web/#/p{property_id}/reports/intelligenthome

중요 안내:
- 권한은 {expiry_str}까지 유효합니다
- 만료 30일, 7일, 1일 전에 알림을 받게 됩니다
- Editor 권한은 7일 후 자동으로 Viewer로 변경됩니다

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
            """
            
            success = self.gmail_sender.send_email(user_email, subject, text_content, html_content)
            
            if success:
                await self._log_notification(user_email, NotificationType.WELCOME, subject)
                self.logger.info(f"✅ 환영 이메일 발송 성공: {user_email}")
            else:
                self.logger.error(f"❌ 환영 이메일 발송 실패: {user_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 환영 이메일 발송 중 오류: {e}")
            return False
    
    async def send_expiry_warning_email(self, user_email: str, property_name: str, 
                                       role: str, expiry_date: datetime, days_left: int) -> bool:
        """만료 경고 이메일 발송"""
        try:
            urgency_level = "high" if days_left <= 3 else "medium" if days_left <= 7 else "low"
            urgency_icon = "🚨" if days_left <= 3 else "⚠️" if days_left <= 7 else "📅"
            urgency_color = "#dc3545" if days_left <= 3 else "#fd7e14" if days_left <= 7 else "#0d6efd"
            
            subject = f"{urgency_icon} [GA4 권한 알림] {days_left}일 후 권한 만료 - {property_name}"
            role_korean = self._get_role_korean(role)
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: {urgency_color}; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">{urgency_icon} 권한 만료 알림</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px; font-weight: bold;">{days_left}일 후 GA4 권한이 만료됩니다</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid {urgency_color}; margin-bottom: 20px;">
                            <h2 style="margin: 0 0 15px 0; color: {urgency_color};">📊 권한 정보</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold; width: 30%;">사용자:</td>
                                    <td style="padding: 8px 0;">{user_email}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold;">프로퍼티:</td>
                                    <td style="padding: 8px 0;">{property_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold;">현재 권한:</td>
                                    <td style="padding: 8px 0;">{role_korean}</td>
                                </tr>
                                <tr style="color: {urgency_color}; font-weight: bold;">
                                    <td style="padding: 8px 0;">만료일:</td>
                                    <td style="padding: 8px 0;">{expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                                </tr>
                                <tr style="color: {urgency_color}; font-weight: bold; font-size: 16px;">
                                    <td style="padding: 8px 0;">남은 시간:</td>
                                    <td style="padding: 8px 0;">{days_left}일</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #155724;">✅ 권한 연장 방법</h3>
                            <ol style="margin: 0; padding-left: 20px;">
                                <li>관리자에게 권한 연장을 요청하세요</li>
                                <li>업무 필요성과 연장 기간을 명시하세요</li>
                                <li>승인 후 자동으로 권한이 연장됩니다</li>
                            </ol>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #856404;">⏰ 만료 후 처리</h3>
                            <p style="margin: 0;">권한이 만료되면:</p>
                            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                                <li>GA4 접근이 자동으로 차단됩니다</li>
                                <li>모든 데이터 접근 권한이 해제됩니다</li>
                                <li>재등록을 위해서는 새로운 신청이 필요합니다</li>
                            </ul>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                            이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
                            발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
{urgency_icon} GA4 권한 만료 알림

{days_left}일 후 GA4 권한이 만료됩니다!

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 현재 권한: {role_korean}
- 만료일: {expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분')}
- 남은 시간: {days_left}일

권한 연장 방법:
1. 관리자에게 권한 연장을 요청하세요
2. 업무 필요성과 연장 기간을 명시하세요
3. 승인 후 자동으로 권한이 연장됩니다

만료 후 처리:
- GA4 접근이 자동으로 차단됩니다
- 모든 데이터 접근 권한이 해제됩니다
- 재등록을 위해서는 새로운 신청이 필요합니다

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
            """
            
            success = self.gmail_sender.send_email(user_email, subject, text_content, html_content)
            
            if success:
                self.logger.info(f"✅ 만료 경고 이메일 발송 성공: {user_email} ({days_left}일 전)")
            else:
                self.logger.error(f"❌ 만료 경고 이메일 발송 실패: {user_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 만료 경고 이메일 발송 중 오류: {e}")
            return False
    
    async def send_deletion_notice_email(self, user_email: str, property_name: str, role: str) -> bool:
        """삭제 알림 이메일 발송"""
        try:
            subject = f"🔒 GA4 권한 만료 및 삭제 완료 - {property_name}"
            role_korean = self._get_role_korean(role)
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #6c757d; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🔒 GA4 권한 만료</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">권한이 만료되어 GA4 접근이 제한되었습니다</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin-bottom: 20px;">
                            <h2 style="margin: 0 0 15px 0; color: #dc3545;">📊 만료된 권한 정보</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold; width: 30%;">사용자:</td>
                                    <td style="padding: 8px 0;">{user_email}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold;">프로퍼티:</td>
                                    <td style="padding: 8px 0;">{property_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold;">이전 권한:</td>
                                    <td style="padding: 8px 0;">{role_korean}</td>
                                </tr>
                                <tr style="color: #dc3545; font-weight: bold;">
                                    <td style="padding: 8px 0;">삭제 시간:</td>
                                    <td style="padding: 8px 0;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background: #f8d7da; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #721c24;">🚫 변경 사항</h3>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>GA4 대시보드 접근이 차단되었습니다</li>
                                <li>모든 데이터 조회 권한이 해제되었습니다</li>
                                <li>보고서 생성 및 내보내기가 불가능합니다</li>
                                <li>계정 설정 변경 권한이 제거되었습니다</li>
                            </ul>
                        </div>
                        
                        <div style="background: #d1ecf1; padding: 20px; border-radius: 8px; border-left: 4px solid #0c5460; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #0c5460;">🔄 재신청 방법</h3>
                            <p style="margin: 0 0 10px 0;">GA4 접근이 다시 필요한 경우:</p>
                            <ol style="margin: 0; padding-left: 20px;">
                                <li>관리자에게 새로운 권한 신청을 요청하세요</li>
                                <li>업무 필요성과 필요한 권한 레벨을 명시하세요</li>
                                <li>승인 후 새로운 권한이 부여됩니다</li>
                            </ol>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                            이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
                            발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
GA4 권한 만료 및 삭제 완료

권한이 만료되어 GA4 접근이 제한되었습니다.

만료된 권한 정보:
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 이전 권한: {role_korean}
- 삭제 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

변경 사항:
- GA4 대시보드 접근이 차단되었습니다
- 모든 데이터 조회 권한이 해제되었습니다
- 보고서 생성 및 내보내기가 불가능합니다
- 계정 설정 변경 권한이 제거되었습니다

재신청 방법:
1. 관리자에게 새로운 권한 신청을 요청하세요
2. 업무 필요성과 필요한 권한 레벨을 명시하세요
3. 승인 후 새로운 권한이 부여됩니다

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
            """
            
            success = self.gmail_sender.send_email(user_email, subject, text_content, html_content)
            
            if success:
                await self._log_notification(user_email, NotificationType.DELETION_NOTICE, subject)
                self.logger.info(f"✅ 삭제 알림 이메일 발송 성공: {user_email}")
            else:
                self.logger.error(f"❌ 삭제 알림 이메일 발송 실패: {user_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 삭제 알림 이메일 발송 중 오류: {e}")
            return False
    
    async def send_admin_notification(self, subject: str, message: str, details: Optional[str] = None) -> bool:
        """관리자 알림 이메일 발송"""
        try:
            admin_email = self.config.get('notification_settings', {}).get('admin_email', 'wonyoungseong@gmail.com')
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #343a40; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🔧 시스템 관리자 알림</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">GA4 권한 관리 시스템에서 중요한 알림이 있습니다</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 20px;">
                            <h2 style="margin: 0 0 15px 0; color: #007bff;">📢 알림 내용</h2>
                            <p style="margin: 0; font-size: 16px; font-weight: bold;">{message}</p>
                        </div>
                        
                        {self._format_details_section(details) if details else ''}
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                            발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}<br>
                            GA4 권한 관리 시스템 자동 알림
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            details_text = f'상세 정보:\n{details}\n' if details else ''
            text_content = f"""
시스템 관리자 알림

알림 내용: {message}

{details_text}

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
GA4 권한 관리 시스템 자동 알림
            """
            
            success = self.gmail_sender.send_email(admin_email, subject, text_content, html_content)
            
            if success:
                await self._log_notification(admin_email, NotificationType.ADMIN_NOTIFICATION, subject)
                self.logger.info(f"✅ 관리자 알림 이메일 발송 성공: {admin_email}")
            else:
                self.logger.error(f"❌ 관리자 알림 이메일 발송 실패: {admin_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 관리자 알림 이메일 발송 중 오류: {e}")
            return False
    
    async def check_and_send_expiry_warnings(self) -> Dict[str, int]:
        """만료 경고 알림 확인 및 발송"""
        try:
            results = {"sent": 0, "failed": 0}
            current_time = datetime.now()
            
            # 30일, 7일, 1일 전 알림 확인
            warning_days = [30, 7, 1]
            
            for days in warning_days:
                target_date = current_time + timedelta(days=days)
                
                # 해당 일수에 만료되는 사용자 조회 (오늘 알림을 보내지 않은 사용자만)
                query = """
                    SELECT ur.등록_계정, ur.property_id, ur.권한, ur.종료일,
                           gp.property_display_name
                    FROM user_registrations ur
                    JOIN ga4_properties gp ON ur.property_id = gp.property_id
                    WHERE ur.status = 'active' 
                    AND ur.종료일 IS NOT NULL
                    AND DATE(ur.종료일) = DATE(?)
                    AND NOT EXISTS (
                        SELECT 1 FROM notification_logs nl 
                        WHERE nl.user_email = ur.등록_계정 
                        AND nl.notification_type = ?
                        AND DATE(nl.sent_at) = DATE(?)
                    )
                """
                
                users = await db_manager.execute_query(
                    query, 
                    (target_date.strftime('%Y-%m-%d'), f"expiry_warning_{days}", current_time.strftime('%Y-%m-%d'))
                )
                
                for user in users:
                    try:
                        user_email = user['등록_계정']
                        property_name = user['property_display_name']
                        role = user['권한']
                        expiry_date = datetime.fromisoformat(user['종료일'])
                        
                        success = await self.send_expiry_warning_email(
                            user_email, property_name, role, expiry_date, days
                        )
                        
                        if success:
                            results["sent"] += 1
                        else:
                            results["failed"] += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ 사용자 {user.get('등록_계정', 'unknown')} 알림 발송 실패: {e}")
                        results["failed"] += 1
            
            self.logger.info(f"📧 만료 알림 발송 완료 - 성공: {results['sent']}, 실패: {results['failed']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 만료 알림 확인 중 오류: {e}")
            return {"sent": 0, "failed": 0, "error": str(e)}
    
    def _get_role_korean(self, role: str) -> str:
        """영문 역할을 한글로 변환"""
        role_mapping = {
            'viewer': '뷰어 (읽기 전용)',
            'analyst': '분석가 (표준 분석)',
            'editor': '편집자 (데이터 수정)',
            'admin': '관리자 (모든 권한)'
        }
        return role_mapping.get(role.lower(), role)
    
    def _format_details_section(self, details: str) -> str:
        """상세 정보 섹션 포맷팅"""
        return f"""
        <div style="background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #495057;">📋 상세 정보</h3>
            <pre style="margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 14px;">{details}</pre>
        </div>
        """
    
    async def send_notification(self, user_email: str, subject: str, text_content: str, html_content: str = None) -> bool:
        """일반 알림 발송"""
        try:
            success = self.gmail_sender.send_email(user_email, subject, text_content, html_content)
            
            if success:
                await self._log_notification(user_email, NotificationType.ADMIN_NOTIFICATION, subject)
                self.logger.info(f"✅ 알림 발송 성공: {user_email}")
            else:
                self.logger.error(f"❌ 알림 발송 실패: {user_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 알림 발송 중 오류: {e}")
            return False

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """호환성을 위한 send_email 메서드"""
        return await self.send_notification(to_email, subject, body)
    
    async def _log_notification(self, user_email: str, notification_type: NotificationType, subject: str):
        """알림 로그 기록"""
        try:
            await db_manager.execute_insert(
                """
                INSERT INTO notification_logs 
                (user_registration_id, user_email, notification_type, sent_to, message_subject, sent_at)
                VALUES (NULL, ?, ?, ?, ?, ?)
                """,
                (user_email, notification_type.value, user_email, subject, datetime.now())
            )
        except Exception as e:
            self.logger.error(f"❌ 알림 로그 기록 실패: {e}")
    
    async def get_notification_stats(self) -> Dict[str, any]:
        """알림 통계 조회"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 총 발송 수
            total_sent_result = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM notification_logs WHERE status = 'sent'"
            )
            total_sent = total_sent_result[0]['count'] if total_sent_result else 0
            
            # 오늘 발송 수
            today_sent_result = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM notification_logs WHERE status = 'sent' AND DATE(sent_at) = ?",
                (current_date,)
            )
            today_sent = today_sent_result[0]['count'] if today_sent_result else 0
            
            # 대기 중인 알림 (만료 예정 사용자)
            pending_result = await db_manager.execute_query(
                """
                SELECT COUNT(*) as count FROM user_registrations 
                WHERE status = 'active' AND 종료일 IS NOT NULL 
                AND DATE(종료일) <= DATE('now', '+30 days')
                """
            )
            pending_notifications = pending_result[0]['count'] if pending_result else 0
            
            # 마지막 발송 시간
            last_sent_result = await db_manager.execute_query(
                "SELECT MAX(sent_at) as last_sent FROM notification_logs WHERE status = 'sent'"
            )
            last_sent = last_sent_result[0]['last_sent'] if last_sent_result and last_sent_result[0]['last_sent'] else None
            
            if last_sent:
                last_sent = datetime.fromisoformat(last_sent).strftime('%m-%d %H:%M')
            
            return {
                'total_sent': total_sent,
                'today_sent': today_sent,
                'pending_notifications': pending_notifications,
                'last_sent': last_sent or '없음'
            }
            
        except Exception as e:
            self.logger.error(f"❌ 알림 통계 조회 중 오류: {e}")
            return {
                'total_sent': 0,
                'today_sent': 0,
                'pending_notifications': 0,
                'last_sent': '오류'
            }
    
    async def process_expiry_notifications(self) -> Dict[str, int]:
        """만료 알림 처리"""
        try:
            results = {"sent": 0, "failed": 0, "skipped": 0}
            current_time = datetime.now()
            
            # 30일, 7일, 1일 전 알림 확인
            warning_days = [30, 7, 1]
            
            for days in warning_days:
                target_date = current_time + timedelta(days=days)
                
                # 해당 일수에 만료되는 사용자 조회 (오늘 알림을 보내지 않은 사용자만)
                query = """
                    SELECT ur.등록_계정 as user_email, ur.property_id, ur.권한 as permission_level, ur.종료일 as expiry_date,
                           gp.property_display_name as property_name
                    FROM user_registrations ur
                    JOIN ga4_properties gp ON ur.property_id = gp.property_id
                    WHERE ur.status = 'active' 
                    AND ur.종료일 IS NOT NULL
                    AND DATE(ur.종료일) = DATE(?)
                    AND NOT EXISTS (
                        SELECT 1 FROM notification_logs nl 
                        WHERE nl.sent_to = ur.등록_계정 
                        AND nl.notification_type = ?
                        AND DATE(nl.sent_at) = DATE(?)
                    )
                """
                
                # 알림 타입 매핑
                notification_type_map = {30: "30_days", 7: "7_days", 1: "1_day"}
                notification_type = notification_type_map.get(days, f"{days}_days")
                
                users = await db_manager.execute_query(
                    query, 
                    (target_date.strftime('%Y-%m-%d'), notification_type, current_time.strftime('%Y-%m-%d'))
                )
                
                for user in users:
                    try:
                        user_email = user['user_email']
                        property_name = user['property_name']
                        role = user['permission_level']
                        expiry_date = datetime.fromisoformat(user['expiry_date'])
                        
                        success = await self.send_expiry_warning_email(
                            user_email, property_name, role, expiry_date, days
                        )
                        
                        if success:
                            # 올바른 알림 타입으로 로그 기록
                            await self._log_notification(
                                user_email, 
                                NotificationType.EXPIRY_WARNING_30 if days == 30 else 
                                NotificationType.EXPIRY_WARNING_7 if days == 7 else 
                                NotificationType.EXPIRY_WARNING_1,
                                f"GA4 권한 {days}일 후 만료 알림"
                            )
                            results["sent"] += 1
                        else:
                            results["failed"] += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ 사용자 {user.get('user_email', 'unknown')} 알림 발송 실패: {e}")
                        results["failed"] += 1
            
            # 당일 만료 알림도 처리
            today_expiry_query = """
                SELECT ur.등록_계정 as user_email, ur.property_id, ur.권한 as permission_level, ur.종료일 as expiry_date,
                       gp.property_display_name as property_name
                FROM user_registrations ur
                JOIN ga4_properties gp ON ur.property_id = gp.property_id
                WHERE ur.status = 'active' 
                AND ur.종료일 IS NOT NULL
                AND DATE(ur.종료일) = DATE(?)
                AND NOT EXISTS (
                    SELECT 1 FROM notification_logs nl 
                    WHERE nl.sent_to = ur.등록_계정 
                    AND nl.notification_type = 'today'
                    AND DATE(nl.sent_at) = DATE(?)
                )
            """
            
            today_users = await db_manager.execute_query(
                today_expiry_query,
                (current_time.strftime('%Y-%m-%d'), current_time.strftime('%Y-%m-%d'))
            )
            
            for user in today_users:
                try:
                    user_email = user['user_email']
                    property_name = user['property_name']
                    role = user['permission_level']
                    expiry_date = datetime.fromisoformat(user['expiry_date'])
                    
                    success = await self.send_expiry_warning_email(
                        user_email, property_name, role, expiry_date, 0
                    )
                    
                    if success:
                        await self._log_notification(
                            user_email, 
                            NotificationType.EXPIRY_TODAY,
                            "GA4 권한 당일 만료 알림"
                        )
                        results["sent"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    self.logger.error(f"❌ 사용자 {user.get('user_email', 'unknown')} 당일 만료 알림 발송 실패: {e}")
                    results["failed"] += 1
            
            self.logger.info(f"📧 만료 알림 발송 완료 - 성공: {results['sent']}, 실패: {results['failed']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 만료 알림 처리 중 오류: {e}")
            return {"sent": 0, "failed": 0, "error": str(e)}
    
    async def send_test_notification(self, email: str, notification_type: str) -> bool:
        """테스트 알림 발송"""
        try:
            # 테스트 데이터
            test_data = {
                "property_name": "테스트 프로퍼티",
                "property_id": "123456789",
                "role": "viewer",
                "expiry_date": datetime.now() + timedelta(days=30),
                "days_left": 7
            }
            
            if notification_type == "welcome":
                success = await self.send_welcome_email(
                    email, 
                    test_data["property_name"], 
                    test_data["property_id"], 
                    test_data["role"], 
                    test_data["expiry_date"]
                )
            elif notification_type.startswith("expiry_warning"):
                days = int(notification_type.split("_")[-1]) if notification_type.split("_")[-1].isdigit() else 7
                success = await self.send_expiry_warning_email(
                    email,
                    test_data["property_name"],
                    test_data["role"],
                    test_data["expiry_date"],
                    days
                )
            elif notification_type == "expiry_today":
                success = await self.send_expiry_warning_email(
                    email,
                    test_data["property_name"],
                    test_data["role"],
                    datetime.now(),
                    0
                )
            elif notification_type == "deletion_notice":
                success = await self.send_deletion_notice_email(
                    email,
                    test_data["property_name"],
                    test_data["role"]
                )
            else:
                self.logger.warning(f"⚠️ 알 수 없는 알림 타입: {notification_type}")
                return False
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 테스트 알림 발송 중 오류: {e}")
            return False
    
    def _create_email_content(self, notification_type: str, user_email: str, data: Dict) -> Dict[str, str]:
        """이메일 콘텐츠 생성"""
        try:
            if notification_type == "welcome":
                subject = f"🎉 GA4 접근 권한이 부여되었습니다 - {data.get('property_name', 'GA4 프로퍼티')}"
                body = f"""
안녕하세요!

GA4 프로퍼티 '{data.get('property_name', 'GA4 프로퍼티')}'에 대한 접근 권한이 부여되었습니다.

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {data.get('property_name', 'GA4 프로퍼티')}
- 권한 레벨: {self._get_role_korean(data.get('role', 'viewer'))}
- 만료일: {data.get('expiry_date', '무제한')}

이제 GA4 대시보드에 접속하여 데이터를 확인하실 수 있습니다.

감사합니다.
GA4 권한 관리 시스템
                """
                
            elif notification_type.startswith("expiry_warning"):
                days_left = data.get('days_left', 7)
                if days_left == 0:
                    subject = f"⚠️ GA4 권한이 오늘 만료됩니다 - {data.get('property_name', 'GA4 프로퍼티')}"
                    urgency = "오늘"
                else:
                    subject = f"⏰ GA4 권한이 {days_left}일 후 만료됩니다 - {data.get('property_name', 'GA4 프로퍼티')}"
                    urgency = f"{days_left}일 후"
                
                body = f"""
안녕하세요!

GA4 프로퍼티 '{data.get('property_name', 'GA4 프로퍼티')}'에 대한 접근 권한이 {urgency} 만료됩니다.

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {data.get('property_name', 'GA4 프로퍼티')}
- 현재 권한: {self._get_role_korean(data.get('role', 'viewer'))}
- 만료일: {data.get('expiry_date', '확인 필요')}

연장이 필요하시면 관리자에게 문의해주세요.

감사합니다.
GA4 권한 관리 시스템
                """
                
            elif notification_type == "deletion_notice":
                subject = f"🚫 GA4 권한이 삭제되었습니다 - {data.get('property_name', 'GA4 프로퍼티')}"
                body = f"""
안녕하세요!

GA4 프로퍼티 '{data.get('property_name', 'GA4 프로퍼티')}'에 대한 접근 권한이 만료되어 삭제되었습니다.

삭제된 권한 정보:
- 사용자: {user_email}
- 프로퍼티: {data.get('property_name', 'GA4 프로퍼티')}
- 이전 권한: {self._get_role_korean(data.get('role', 'viewer'))}
- 삭제 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

재신청이 필요하시면 관리자에게 문의해주세요.

감사합니다.
GA4 권한 관리 시스템
                """
            else:
                subject = "GA4 권한 관리 시스템 알림"
                body = f"사용자 {user_email}에게 알림이 발송되었습니다."
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            self.logger.error(f"❌ 이메일 콘텐츠 생성 중 오류: {e}")
            return {
                "subject": "GA4 권한 관리 시스템 알림",
                "body": "알림 내용을 생성하는 중 오류가 발생했습니다."
            }


    async def check_and_send_daily_notifications(self) -> Dict[str, int]:
        """일일 알림 확인 및 발송 (스케줄러에서 호출)"""
        try:
            self.logger.info("📅 일일 알림 확인 시작...")
            
            results = {
                "expiry_warnings_sent": 0,
                "expiry_notifications_sent": 0,
                "failed": 0
            }
            
            # 1. 만료 경고 알림 확인 및 발송
            expiry_warnings = await self.check_and_send_expiry_warnings()
            results["expiry_warnings_sent"] = expiry_warnings.get("sent", 0)
            results["failed"] += expiry_warnings.get("failed", 0)
            
            # 2. 당일 만료 알림 확인 및 발송
            expiry_notifications = await self.process_expiry_notifications()
            results["expiry_notifications_sent"] = expiry_notifications.get("sent", 0)
            results["failed"] += expiry_notifications.get("failed", 0)
            
            self.logger.info(f"✅ 일일 알림 확인 완료 - 경고: {results['expiry_warnings_sent']}, 만료: {results['expiry_notifications_sent']}, 실패: {results['failed']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 일일 알림 확인 실패: {e}")
            return {"expiry_warnings_sent": 0, "expiry_notifications_sent": 0, "failed": 1}

    async def check_and_send_expiry_notifications(self) -> Dict[str, int]:
        """만료 알림 확인 및 발송 (스케줄러 호환)"""
        return await self.check_and_send_daily_notifications()

    async def send_editor_downgrade_notification(self, user_data: Dict[str, Any]) -> bool:
        """Editor 권한 다운그레이드 알림 발송"""
        try:
            user_email = user_data.get('user_email', '')
            property_name = user_data.get('property_name', '')
            applicant = user_data.get('applicant', '')
            
            subject = f"📉 [GA4 권한 변경] Editor → Viewer 자동 다운그레이드 - {property_name}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #fd7e14; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">📉 권한 변경 알림</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Editor 권한이 Viewer로 자동 변경되었습니다</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800; margin-bottom: 20px;">
                            <h2 style="margin: 0 0 15px 0; color: #e65100;">📊 변경된 권한 정보</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr style="background: white;">
                                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; width: 30%;">신청자</td>
                                    <td style="padding: 12px; border: 1px solid #dee2e6;">{applicant}</td>
                                </tr>
                                <tr style="background: #f8f9fa;">
                                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">사용자</td>
                                    <td style="padding: 12px; border: 1px solid #dee2e6;">{user_email}</td>
                                </tr>
                                <tr style="background: white;">
                                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">프로퍼티</td>
                                    <td style="padding: 12px; border: 1px solid #dee2e6;">{property_name}</td>
                                </tr>
                                <tr style="background: #f8f9fa;">
                                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">이전 권한</td>
                                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="color: #dc3545; font-weight: bold;">Editor</span></td>
                                </tr>
                                <tr style="background: white;">
                                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">현재 권한</td>
                                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="color: #28a745; font-weight: bold;">Viewer</span></td>
                                </tr>
                                <tr style="background: #f8f9fa;">
                                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">변경 시간</td>
                                    <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #1565c0;">ℹ️ 변경 사유</h3>
                            <p style="margin: 0;">Editor 권한은 보안상의 이유로 7일 후 자동으로 Viewer 권한으로 변경됩니다.</p>
                            <p style="margin: 10px 0 0 0;">계속해서 Editor 권한이 필요한 경우 관리자에게 재신청을 요청해주세요.</p>
                        </div>
                        
                        <div style="background: #f1f8e9; padding: 20px; border-radius: 8px; border-left: 4px solid #4caf50; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #2e7d32;">✅ Viewer 권한으로도 가능한 작업</h3>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>모든 보고서 및 데이터 조회</li>
                                <li>대시보드 생성 및 공유</li>
                                <li>커스텀 보고서 작성</li>
                                <li>데이터 내보내기</li>
                            </ul>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                            이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
                            발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
GA4 권한 변경 알림

안녕하세요, {applicant}님!

Google Analytics 4 Editor 권한이 Viewer로 자동 변경되었습니다.

변경 정보:
- 신청자: {applicant}
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 이전 권한: Editor
- 현재 권한: Viewer
- 변경 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

변경 사유:
Editor 권한은 보안상의 이유로 7일 후 자동으로 Viewer 권한으로 변경됩니다.
계속해서 Editor 권한이 필요한 경우 관리자에게 재신청을 요청해주세요.

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
            """
            
            success = self.gmail_sender.send_email(user_email, subject, text_content, html_content)
            
            if success:
                await self._log_notification(user_email, NotificationType.EDITOR_AUTO_DOWNGRADE, subject)
                self.logger.info(f"✅ Editor 다운그레이드 알림 발송 성공: {user_email}")
            else:
                self.logger.error(f"❌ Editor 다운그레이드 알림 발송 실패: {user_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Editor 다운그레이드 알림 발송 중 오류: {e}")
            return False

    async def send_immediate_approval_notification(self, registration_data: Dict) -> bool:
        """즉시 승인 알림 발송"""
        try:
            # 알림 설정 확인
            notification_setting = await self.db_manager.execute_query(
                "SELECT * FROM notification_settings WHERE notification_type = 'immediate_approval' AND enabled = 1"
            )
            
            if not notification_setting:
                self.logger.info("즉시 승인 알림이 비활성화되어 있습니다.")
                return False
            
            # 담당자 목록 조회
            responsible_persons = await self.db_manager.get_responsible_persons(
                property_id=registration_data.get('property_id'),
                account_id=registration_data.get('account_id')
            )
            
            if not responsible_persons:
                self.logger.warning("담당자가 설정되지 않았습니다.")
                return False
            
            # 이메일 내용 구성
            setting = notification_setting[0]
            subject = setting['template_subject']
            
            body = f"""
            새로운 GA4 권한 신청이 있습니다.
            
            신청자: {registration_data.get('신청자', 'N/A')}
            등록 계정: {registration_data.get('등록_계정', 'N/A')}
            프로퍼티 ID: {registration_data.get('property_id', 'N/A')}
            권한: {registration_data.get('권한', 'N/A')}
            종료일: {registration_data.get('종료일', 'N/A')}
            
            승인이 필요한 경우 관리자 페이지에서 처리해 주세요.
            """
            
            # 담당자들에게 이메일 발송
            success_count = 0
            for person in responsible_persons:
                try:
                    success = await self.send_email(
                        to_email=person['email'],
                        subject=subject,
                        body=body
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"✅ 즉시 알림 발송 성공: {person['email']}")
                    else:
                        self.logger.warning(f"⚠️ 즉시 알림 발송 실패: {person['email']}")
                except Exception as e:
                    self.logger.error(f"❌ 즉시 알림 발송 오류 ({person['email']}): {e}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ 즉시 승인 알림 발송 실패: {e}")
            return False

    async def send_daily_summary_notification(self) -> bool:
        """일일 요약 알림 발송"""
        try:
            # 알림 설정 확인
            notification_setting = await self.db_manager.execute_query(
                "SELECT * FROM notification_settings WHERE notification_type = 'daily_summary' AND enabled = 1"
            )
            
            if not notification_setting:
                self.logger.info("일일 요약 알림이 비활성화되어 있습니다.")
                return False
            
            # 오늘의 신청 목록 조회
            today = datetime.now().strftime('%Y-%m-%d')
            today_registrations = await self.db_manager.execute_query(
                """SELECT * FROM user_registrations 
                   WHERE DATE(신청일) = ? 
                   ORDER BY 신청일 DESC""",
                (today,)
            )
            
            if not today_registrations:
                self.logger.info("오늘 신청된 권한이 없습니다.")
                return False
            
            # 담당자 목록 조회 (전체)
            responsible_persons = await self.db_manager.get_responsible_persons()
            
            if not responsible_persons:
                self.logger.warning("담당자가 설정되지 않았습니다.")
                return False
            
            # 이메일 내용 구성
            setting = notification_setting[0]
            subject = f"{setting['template_subject']} - {today}"
            
            body = f"""
            {today} GA4 권한 신청 일일 요약
            
            총 신청 건수: {len(today_registrations)}건
            
            """
            
            # 신청 목록 추가
            for i, reg in enumerate(today_registrations, 1):
                body += f"""
            {i}. 신청자: {reg.get('신청자', 'N/A')}
               등록 계정: {reg.get('등록_계정', 'N/A')}
               프로퍼티 ID: {reg.get('property_id', 'N/A')}
               권한: {reg.get('권한', 'N/A')}
               상태: {reg.get('status', 'N/A')}
               신청일시: {reg.get('신청일', 'N/A')}
            """
            
            body += f"""
            
            승인이 필요한 신청이 있는 경우 관리자 페이지에서 처리해 주세요.
            """
            
            # 담당자들에게 이메일 발송
            success_count = 0
            for person in responsible_persons:
                try:
                    success = await self.send_email(
                        to_email=person['email'],
                        subject=subject,
                        body=body
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"✅ 일일 요약 발송 성공: {person['email']}")
                    else:
                        self.logger.warning(f"⚠️ 일일 요약 발송 실패: {person['email']}")
                except Exception as e:
                    self.logger.error(f"❌ 일일 요약 발송 오류 ({person['email']}): {e}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ 일일 요약 알림 발송 실패: {e}")
            return False


# 전역 인스턴스
notification_service = NotificationService()