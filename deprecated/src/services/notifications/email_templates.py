#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이메일 템플릿 매니저
=================

이메일 템플릿 생성과 관리를 담당하는 클래스입니다.
단일 책임 원칙(SRP)에 따라 템플릿 관련 로직만 포함합니다.
"""

from datetime import datetime
from typing import Dict, Any, Tuple
from .notification_types import NotificationType


class EmailTemplateManager:
    """이메일 템플릿 생성 및 관리 클래스
    
    모든 이메일 템플릿을 중앙에서 관리하며,
    일관된 디자인과 구조를 제공합니다.
    """
    
    @staticmethod
    def _get_role_korean(role: str) -> str:
        """영문 역할을 한글로 변환"""
        role_mapping = {
            'viewer': '뷰어 (읽기 전용)',
            'analyst': '분석가 (표준 분석)', 
            'editor': '편집자 (데이터 수정)',
            'admin': '관리자 (모든 권한)'
        }
        return role_mapping.get(role.lower(), role)
    
    @staticmethod
    def _get_base_template() -> str:
        """기본 HTML 템플릿 구조"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {header}
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    {content}
                    {footer}
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_header_template(title: str, subtitle: str, color: str = "#667eea") -> str:
        """헤더 템플릿"""
        return f"""
        <div style="background: linear-gradient(135deg, {color} 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="margin: 0; font-size: 28px;">{title}</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{subtitle}</p>
        </div>
        """
    
    @staticmethod
    def _get_footer_template() -> str:
        """푸터 템플릿"""
        return f"""
        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
        <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
            이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
            발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
        </p>
        """
    
    @classmethod
    def create_welcome_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """환영 이메일 템플릿 생성"""
        
        user_email = user_data.get('user_email', user_data.get('email', ''))
        property_name = user_data.get('property_name', '알 수 없음')
        property_id = user_data.get('property_id', '')
        role = user_data.get('role', 'viewer')
        expiry_date = user_data.get('expiry_date')
        
        expiry_str = expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else "무제한"
        role_korean = cls._get_role_korean(role)
        subject = f"🎉 GA4 권한 부여 완료 - {property_name}"
        
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

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content
    
    @classmethod
    def create_expiry_warning_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """만료 경고 이메일 템플릿 생성"""
        
        user_email = user_data.get('user_email', user_data.get('email', ''))
        property_name = user_data.get('property_name', '알 수 없음')
        role = user_data.get('role', 'viewer')
        expiry_date = user_data.get('expiry_date')
        days_left = user_data.get('days_left', 0)
        
        urgency_level = "high" if days_left <= 3 else "medium" if days_left <= 7 else "low"
        urgency_icon = "🚨" if days_left <= 3 else "⚠️" if days_left <= 7 else "📅"
        urgency_color = "#dc3545" if days_left <= 3 else "#fd7e14" if days_left <= 7 else "#0d6efd"
        
        subject = f"{urgency_icon} [GA4 권한 알림] {days_left}일 후 권한 만료 - {property_name}"
        role_korean = cls._get_role_korean(role)
        
        header = cls._get_header_template(
            f"{urgency_icon} 권한 만료 알림",
            f"{days_left}일 후 GA4 권한이 만료됩니다",
            urgency_color
        )
        
        content = f"""
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
                    <td style="padding: 8px 0;">{expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분') if expiry_date else '미설정'}</td>
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
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        text_content = f"""
{urgency_icon} GA4 권한 만료 알림

{days_left}일 후 GA4 권한이 만료됩니다!

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 현재 권한: {role_korean}
- 만료일: {expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분') if expiry_date else '미설정'}
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
        
        return subject, text_content, html_content
    
    @classmethod
    def create_expiry_warning_30_days_email(cls, user_email: str, property_name: str,
                                           property_id: str, role: str, expiry_date: datetime) -> Tuple[str, str, str]:
        """30일 전 만료 경고 이메일 템플릿 생성 (별도 디자인)"""
        
        subject = f"📅 [GA4 권한 알림] 30일 후 권한 만료 예정 - {property_name}"
        role_korean = cls._get_role_korean(role)
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #0d6efd 0%, #0056b3 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">📅 권한 만료 안내</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">30일 후 GA4 권한이 만료됩니다</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #0d6efd; margin-bottom: 25px;">
                        <h2 style="margin: 0 0 15px 0; color: #0d6efd;">📊 권한 정보</h2>
                        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden;">
                            <tr>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6; font-weight: bold; width: 30%; background: #f8f9fa;">사용자</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{user_email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6; font-weight: bold; background: #f8f9fa;">프로퍼티</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{property_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6; font-weight: bold; background: #f8f9fa;">권한 레벨</td>
                                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{role_korean}</td>
                            </tr>
                            <tr style="color: #0d6efd; font-weight: bold;">
                                <td style="padding: 12px; background: #f8f9fa;">만료일</td>
                                <td style="padding: 12px;">{expiry_date.strftime('%Y년 %m월 %d일 %H시')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <h3 style="margin: 0 0 15px 0; color: #856404;">⏰ 연장 안내</h3>
                        <p style="margin: 0 0 15px 0; color: #856404;">권한이 필요하시다면 <strong>지금 연장 신청</strong>을 해주세요:</p>
                        <ul style="margin: 0; padding-left: 20px; color: #856404;">
                            <li>관리자에게 권한 연장 요청</li>
                            <li>업무 필요성과 연장 기간 명시</li>
                            <li>승인 후 자동으로 기간 연장</li>
                        </ul>
                    </div>
                    
                    <div style="background: #d1ecf1; padding: 20px; border-radius: 8px; border-left: 4px solid #17a2b8; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #0c5460;">🔗 빠른 접속</h3>
                        <p style="margin: 0 0 15px 0; color: #0c5460;">현재 권한으로 GA4에 접속하여 작업을 계속하세요:</p>
                        <a href="https://analytics.google.com/analytics/web/#/p{property_id}/reports/intelligenthome" 
                           style="background: #17a2b8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            📈 GA4 바로가기
                        </a>
                    </div>
                    
                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <p style="margin: 0; color: #721c24; font-weight: bold;">
                            ⚠️ 만료 후에는 자동으로 권한이 삭제되며, 재신청이 필요합니다.
                        </p>
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
GA4 권한 만료 안내 (30일 전)

안녕하세요, {user_email}님!

30일 후 Google Analytics 4 권한이 만료될 예정입니다.

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 권한 레벨: {role_korean}
- 만료일: {expiry_date.strftime('%Y년 %m월 %d일 %H시')}

연장이 필요하시다면:
1. 관리자에게 권한 연장을 요청하세요
2. 업무 필요성과 연장 기간을 명시하세요
3. 승인 후 자동으로 기간이 연장됩니다

GA4 접속: https://analytics.google.com/analytics/web/#/p{property_id}/reports/intelligenthome

⚠️ 만료 후에는 자동으로 권한이 삭제되며, 재신청이 필요합니다.

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content
    
    @classmethod
    def create_deletion_notice_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """삭제 알림 이메일 템플릿 생성"""
        
        user_email = user_data.get('user_email', '')
        property_name = user_data.get('property_name', '')
        role = user_data.get('role', 'viewer')
        
        subject = f"🔒 GA4 권한 만료 및 삭제 완료 - {property_name}"
        role_korean = cls._get_role_korean(role)
        
        header = cls._get_header_template(
            "🔒 GA4 권한 만료",
            "권한이 만료되어 GA4 접근이 제한되었습니다",
            "#6c757d"
        )
        
        content = f"""
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
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
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
        
        return subject, text_content, html_content
    
    @classmethod
    def create_admin_notification_email(cls, subject: str = "🔧 GA4 시스템 알림", message: str = "시스템 알림", details: str = None) -> Tuple[str, str, str]:
        """관리자 알림 이메일 템플릿 생성"""
        
        header = cls._get_header_template(
            "🔧 시스템 관리자 알림",
            "GA4 권한 관리 시스템에서 중요한 알림이 있습니다",
            "#343a40"
        )
        
        details_section = ""
        if details:
            details_section = f"""
            <div style="background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #495057;">📋 상세 정보</h3>
                <pre style="margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 14px;">{details}</pre>
            </div>
            """
        
        content = f"""
        <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #007bff;">📢 알림 내용</h2>
            <p style="margin: 0; font-size: 16px; font-weight: bold;">{message}</p>
        </div>
        {details_section}
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        details_text = f'상세 정보:\n{details}\n' if details else ''
        text_content = f"""
시스템 관리자 알림

알림 내용: {message}

{details_text}

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
GA4 권한 관리 시스템 자동 알림
        """
        
        return subject, text_content, html_content
    
    @classmethod
    def create_editor_downgrade_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Editor 다운그레이드 이메일 템플릿 생성"""
        
        user_email = user_data.get('user_email', '')
        property_name = user_data.get('property_name', '')
        applicant = user_data.get('applicant', '')
        
        subject = f"📉 [GA4 권한 변경] Editor → Viewer 자동 다운그레이드 - {property_name}"
        
        header = cls._get_header_template(
            "📉 권한 변경 알림",
            "Editor 권한이 Viewer로 자동 변경되었습니다",
            "#fd7e14"
        )
        
        content = f"""
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
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        applicant_text = f"신청자: {applicant}\n" if applicant and applicant != user_email else ""
        
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
        
        return subject, text_content, html_content
    
    @classmethod
    def create_editor_approved_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Editor 권한 승인 이메일 템플릿 생성"""
        
        user_email = user_data.get('user_email', '')
        property_name = user_data.get('property_name', '')
        property_id = user_data.get('property_id', '')
        expiry_date = user_data.get('expiry_date')
        applicant = user_data.get('applicant')
        
        subject = f"🎉 [GA4 권한 승인] Editor 권한 승인 완료 - {property_name}"
        
        header = cls._get_header_template(
            "🎉 Editor 권한 승인",
            "Editor 권한이 성공적으로 승인되었습니다",
            "#28a745"
        )
        
        applicant_info = ""
        if applicant and applicant != user_email:
            applicant_info = f"""
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">신청자</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{applicant}</td>
                </tr>
            """
        
        content = f"""
        <div style="background: #d4edda; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #155724;">🎯 승인된 권한 정보</h2>
            <table style="width: 100%; border-collapse: collapse;">
                {applicant_info}
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
                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="background: #ff9800; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">Editor</span></td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">승인 시간</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">권한 만료일</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">{expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else '미설정'}</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #e65100;">🚨 중요 안내사항</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>권한 유효기간:</strong> Editor 권한은 7일간 유효합니다</li>
                <li><strong>자동 다운그레이드:</strong> 7일 후 자동으로 Viewer 권한으로 변경됩니다</li>
                <li><strong>지속적 사용:</strong> 계속 필요한 경우 만료 전 재신청해주세요</li>
                <li><strong>보안 주의:</strong> Editor 권한은 신중하게 사용해주세요</li>
            </ul>
        </div>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #1565c0;">✅ Editor 권한으로 가능한 작업</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>모든 보고서 및 데이터 조회 (Viewer 권한과 동일)</li>
                <li>속성 및 보기 설정 변경</li>
                <li>목표 및 전환 설정 관리</li>
                <li>사용자 정의 정의 및 계산된 측정항목 생성</li>
                <li>필터 및 세그먼트 생성/수정</li>
                <li>링크된 제품 관리 (Google Ads 연동 등)</li>
            </ul>
        </div>
        
        <div style="background: #f8d7da; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #721c24;">⚠️ 사용 시 주의사항</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>설정 변경 시 충분히 검토 후 실행해주세요</li>
                <li>중요한 변경사항은 팀원들과 사전 공유해주세요</li>
                <li>테스트는 별도 환경에서 진행해주세요</li>
                <li>권한 만료 전 필요 시 재신청을 미리 요청해주세요</li>
            </ul>
        </div>
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        applicant_text = f"신청자: {applicant}\n" if applicant and applicant != user_email else ""
        
        text_content = f"""
GA4 Editor 권한 승인 완료

안녕하세요! Google Analytics 4 Editor 권한이 승인되었습니다.

승인된 권한 정보:
{applicant_text}사용자: {user_email}
프로퍼티: {property_name}
권한 레벨: Editor
승인 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
권한 만료일: {expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else '미설정'}

중요 안내사항:
- 권한 유효기간: Editor 권한은 7일간 유효합니다
- 자동 다운그레이드: 7일 후 자동으로 Viewer 권한으로 변경됩니다
- 지속적 사용: 계속 필요한 경우 만료 전 재신청해주세요
- 보안 주의: Editor 권한은 신중하게 사용해주세요

Editor 권한으로 가능한 작업:
- 모든 보고서 및 데이터 조회 (Viewer 권한과 동일)
- 속성 및 보기 설정 변경
- 목표 및 전환 설정 관리
- 사용자 정의 정의 및 계산된 측정항목 생성
- 필터 및 세그먼트 생성/수정
- 링크된 제품 관리 (Google Ads 연동 등)

사용 시 주의사항:
- 설정 변경 시 충분히 검토 후 실행해주세요
- 중요한 변경사항은 팀원들과 사전 공유해주세요
- 테스트는 별도 환경에서 진행해주세요
- 권한 만료 전 필요 시 재신청을 미리 요청해주세요

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content
    
    @classmethod
    def create_admin_approved_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Admin 권한 승인 이메일 템플릿 생성"""
        
        user_email = user_data.get('user_email', '')
        property_name = user_data.get('property_name', '')
        property_id = user_data.get('property_id', '')
        expiry_date = user_data.get('expiry_date')
        applicant = user_data.get('applicant')
        
        subject = f"🚀 [GA4 권한 승인] Admin 권한 승인 완료 - {property_name}"
        
        header = cls._get_header_template(
            "🚀 Admin 권한 승인",
            "Admin 권한이 성공적으로 승인되었습니다",
            "#dc3545"
        )
        
        applicant_info = ""
        if applicant and applicant != user_email:
            applicant_info = f"""
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">신청자</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{applicant}</td>
                </tr>
            """
        
        content = f"""
        <div style="background: #f8d7da; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #721c24;">🎯 승인된 권한 정보</h2>
            <table style="width: 100%; border-collapse: collapse;">
                {applicant_info}
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
                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">Admin</span></td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">승인 시간</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">권한 만료일</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">{expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else '미설정'}</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #e65100;">🚨 중요 안내사항</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>권한 유효기간:</strong> Admin 권한은 7일간 유효합니다</li>
                <li><strong>자동 다운그레이드:</strong> 7일 후 자동으로 Viewer 권한으로 변경됩니다</li>
                <li><strong>지속적 사용:</strong> 계속 필요한 경우 만료 전 재신청해주세요</li>
                <li><strong>보안 주의:</strong> Admin 권한은 최고 권한이므로 매우 신중하게 사용해주세요</li>
            </ul>
        </div>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #1565c0;">✅ Admin 권한으로 가능한 작업</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>모든 보고서 및 데이터 조회 (Viewer, Editor 권한 포함)</li>
                <li>속성 및 보기 설정 변경</li>
                <li>목표 및 전환 설정 관리</li>
                <li>사용자 정의 정의 및 계산된 측정항목 생성</li>
                <li>필터 및 세그먼트 생성/수정</li>
                <li>링크된 제품 관리 (Google Ads 연동 등)</li>
                <li><strong>사용자 관리 및 권한 부여</strong></li>
                <li><strong>계정 설정 및 구성 관리</strong></li>
                <li><strong>데이터 스트림 관리</strong></li>
                <li><strong>고급 분석 기능 접근</strong></li>
            </ul>
        </div>
        
        <div style="background: #f8d7da; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #721c24;">⚠️ 사용 시 주의사항</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>Admin 권한은 최고 권한이므로 매우 신중하게 사용해주세요</li>
                <li>중요한 설정 변경 시 반드시 팀원들과 사전 협의해주세요</li>
                <li>사용자 권한 부여 시 최소 권한 원칙을 적용해주세요</li>
                <li>데이터 삭제나 구성 변경 시 백업을 확인해주세요</li>
                <li>권한 만료 전 필요 시 재신청을 미리 요청해주세요</li>
            </ul>
        </div>
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        applicant_text = f"신청자: {applicant}\n" if applicant and applicant != user_email else ""
        
        text_content = f"""
GA4 Admin 권한 승인 완료

안녕하세요! Google Analytics 4 Admin 권한이 승인되었습니다.

승인된 권한 정보:
{applicant_text}사용자: {user_email}
프로퍼티: {property_name}
권한 레벨: Admin
승인 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
권한 만료일: {expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else '미설정'}

중요 안내사항:
- 권한 유효기간: Admin 권한은 7일간 유효합니다
- 자동 다운그레이드: 7일 후 자동으로 Viewer 권한으로 변경됩니다
- 지속적 사용: 계속 필요한 경우 만료 전 재신청해주세요
- 보안 주의: Admin 권한은 최고 권한이므로 매우 신중하게 사용해주세요

Admin 권한으로 가능한 작업:
- 모든 보고서 및 데이터 조회 (Viewer, Editor 권한 포함)
- 속성 및 보기 설정 변경
- 목표 및 전환 설정 관리
- 사용자 정의 정의 및 계산된 측정항목 생성
- 필터 및 세그먼트 생성/수정
- 링크된 제품 관리 (Google Ads 연동 등)
- 사용자 관리 및 권한 부여
- 계정 설정 및 구성 관리
- 데이터 스트림 관리
- 고급 분석 기능 접근

사용 시 주의사항:
- Admin 권한은 최고 권한이므로 매우 신중하게 사용해주세요
- 중요한 설정 변경 시 반드시 팀원들과 사전 협의해주세요
- 사용자 권한 부여 시 최소 권한 원칙을 적용해주세요
- 데이터 삭제나 구성 변경 시 백업을 확인해주세요
- 권한 만료 전 필요 시 재신청을 미리 요청해주세요

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content

    @classmethod
    def create_deletion_notification_email(cls, user_email: str, account_email: str, 
                                         property_name: str, expiry_date: str) -> str:
        """삭제 알림 이메일 생성"""
        return f"""
안녕하세요,

{property_name} GA4 프로퍼티에서 {account_email} 계정의 접근 권한이 만료되어 자동으로 제거되었습니다.

▶ 제거된 계정: {account_email}
▶ 프로퍼티: {property_name}
▶ 만료일: {expiry_date}
▶ 제거일: {datetime.now().strftime('%Y-%m-%d %H:%M')}

다시 접근이 필요한 경우 관리자에게 문의해주세요.

감사합니다.
        """.strip()

    @classmethod
    def create_pending_approval_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """승인 대기 이메일 템플릿 생성"""
        user_email = user_data.get('user_email', user_data.get('email', ''))
        property_name = user_data.get('property_name', '알 수 없음')
        role = user_data.get('role', 'viewer')
        applicant = user_data.get('applicant', '')
        role_korean = cls._get_role_korean(role)
        
        subject = f"📋 [GA4 {role.upper()} 권한 신청] {property_name} - 승인 대기 중입니다"
        
        header = cls._get_header_template(
            "📋 권한 신청 접수",
            "귀하의 GA4 권한 신청이 접수되어 승인 대기 중입니다",
            "#ffc107"
        )
        
        applicant_info = ""
        if applicant and applicant != user_email:
            applicant_info = f"""
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">신청자</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{applicant}</td>
                </tr>
            """
        
        content = f"""
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #e65100;">📋 신청 정보</h2>
            <table style="width: 100%; border-collapse: collapse;">
                {applicant_info}
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; width: 30%;">사용자</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{user_email}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">프로퍼티</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{property_name}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">신청 권한</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="background: #ffc107; color: #212529; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{role_korean}</span></td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">신청 시간</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">상태</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; color: #ffc107; font-weight: bold;">승인 대기 중</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #1565c0;">⏳ 다음 단계</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>관리자가 귀하의 신청을 검토하고 있습니다</li>
                <li>승인 완료 시 별도 이메일로 안내해드립니다</li>
                <li>일반적으로 1-2 영업일 내에 처리됩니다</li>
                <li>추가 문의사항은 관리자에게 연락해주세요</li>
            </ul>
        </div>
        
        <div style="background: #f1f8e9; padding: 20px; border-radius: 8px; border-left: 4px solid #4caf50; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #2e7d32;">📋 {role_korean} 권한 안내</h3>
            <p style="margin: 0;">승인 완료 시 다음과 같은 권한을 사용하실 수 있습니다:</p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                {"<li>모든 보고서 및 데이터 조회</li><li>대시보드 생성 및 공유</li><li>커스텀 보고서 작성</li>" if role == 'viewer' else ""}
                {"<li>모든 보고서 및 데이터 조회</li><li>고급 분석 및 세그먼트 생성</li><li>커스텀 보고서 및 대시보드 생성</li>" if role == 'analyst' else ""}
                {"<li>모든 보고서 및 데이터 조회</li><li>속성 및 보기 설정 변경</li><li>목표 및 전환 설정 관리</li><li>사용자 정의 정의 생성</li>" if role == 'editor' else ""}
                {"<li>모든 보고서 및 데이터 조회</li><li>속성 및 보기 설정 변경</li><li>사용자 관리 및 권한 부여</li><li>계정 설정 관리</li>" if role == 'admin' else ""}
            </ul>
        </div>
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        applicant_text = f"신청자: {applicant}\n" if applicant and applicant != user_email else ""
        
        text_content = f"""
GA4 권한 신청 접수

안녕하세요! GA4 권한 신청이 접수되어 승인 대기 중입니다.

신청 정보:
{applicant_text}사용자: {user_email}
프로퍼티: {property_name}
신청 권한: {role_korean}
신청 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
상태: 승인 대기 중

다음 단계:
- 관리자가 귀하의 신청을 검토하고 있습니다
- 승인 완료 시 별도 이메일로 안내해드립니다
- 일반적으로 1-2 영업일 내에 처리됩니다
- 추가 문의사항은 관리자에게 연락해주세요

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content

    @classmethod
    def create_test_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """테스트 이메일 템플릿 생성"""
        user_email = user_data.get('user_email', user_data.get('email', ''))
        test_type = user_data.get('test_type', 'general')
        
        subject = f"🧪 [GA4 테스트] 알림 시스템 테스트 - {datetime.now().strftime('%H:%M:%S')}"
        
        header = cls._get_header_template(
            "🧪 시스템 테스트",
            "GA4 권한 관리 시스템의 알림 기능을 테스트합니다",
            "#6f42c1"
        )
        
        content = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #6f42c1; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #6f42c1;">🧪 테스트 정보</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; width: 30%;">수신자</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{user_email}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">테스트 유형</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{test_type}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">발송 시간</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">상태</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 4px;">정상 작동</span></td>
                </tr>
            </table>
        </div>
        
        <div style="background: #d4edda; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #155724;">✅ 테스트 결과</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li>이메일 발송 시스템: 정상 작동</li>
                <li>HTML 템플릿 렌더링: 정상 작동</li>
                <li>데이터베이스 연결: 정상 작동</li>
                <li>알림 로그 기록: 정상 작동</li>
            </ul>
        </div>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #1565c0;">📊 시스템 정보</h3>
            <p style="margin: 0;">이 테스트 이메일이 정상적으로 수신되었다면 GA4 권한 관리 시스템의 알림 기능이 정상적으로 작동하고 있습니다.</p>
        </div>
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        text_content = f"""
GA4 시스템 테스트

안녕하세요! GA4 권한 관리 시스템의 알림 기능을 테스트합니다.

테스트 정보:
수신자: {user_email}
테스트 유형: {test_type}
발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}
상태: 정상 작동

테스트 결과:
- 이메일 발송 시스템: 정상 작동
- HTML 템플릿 렌더링: 정상 작동
- 데이터베이스 연결: 정상 작동
- 알림 로그 기록: 정상 작동

이 테스트 이메일이 정상적으로 수신되었다면 GA4 권한 관리 시스템의 알림 기능이 정상적으로 작동하고 있습니다.

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content

    @classmethod
    def create_extension_approved_email(cls, user_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """권한 연장 승인 이메일 템플릿 생성"""
        user_email = user_data.get('user_email', user_data.get('email', ''))
        property_name = user_data.get('property_name', '알 수 없음')
        role = user_data.get('role', 'viewer')
        expiry_date = user_data.get('expiry_date')
        previous_expiry = user_data.get('previous_expiry_date')
        role_korean = cls._get_role_korean(role)
        
        subject = f"🔄 [GA4 권한 연장] {property_name} 권한 연장 승인 완료"
        
        header = cls._get_header_template(
            "🔄 권한 연장 승인",
            "GA4 권한이 성공적으로 연장되었습니다",
            "#17a2b8"
        )
        
        content = f"""
        <div style="background: #d1ecf1; padding: 20px; border-radius: 8px; border-left: 4px solid #17a2b8; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #0c5460;">🔄 연장된 권한 정보</h2>
            <table style="width: 100%; border-collapse: collapse;">
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
                    <td style="padding: 12px; border: 1px solid #dee2e6;"><span style="background: #17a2b8; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{role_korean}</span></td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">연장 승인 시간</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                </tr>
                {"<tr style='background: white;'><td style='padding: 12px; border: 1px solid #dee2e6; font-weight: bold;'>이전 만료일</td><td style='padding: 12px; border: 1px solid #dee2e6; color: #dc3545;'>" + str(previous_expiry) + "</td></tr>" if previous_expiry else ""}
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">새 만료일</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; color: #28a745; font-weight: bold;">{expiry_date if expiry_date else '미설정'}</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #d4edda; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #155724;">✅ 연장 완료</h3>
            <p style="margin: 0;">귀하의 GA4 권한이 성공적으로 연장되었습니다. 계속해서 GA4 서비스를 이용하실 수 있습니다.</p>
        </div>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #1565c0;">📋 권한 안내</h3>
            <p style="margin: 0 0 10px 0;">{role_korean} 권한으로 다음과 같은 작업을 수행하실 수 있습니다:</p>
            <ul style="margin: 0; padding-left: 20px;">
                {"<li>모든 보고서 및 데이터 조회</li><li>대시보드 생성 및 공유</li><li>커스텀 보고서 작성</li>" if role == 'viewer' else ""}
                {"<li>모든 보고서 및 데이터 조회</li><li>고급 분석 및 세그먼트 생성</li><li>커스텀 보고서 및 대시보드 생성</li>" if role == 'analyst' else ""}
                {"<li>모든 보고서 및 데이터 조회</li><li>속성 및 보기 설정 변경</li><li>목표 및 전환 설정 관리</li><li>사용자 정의 정의 생성</li>" if role == 'editor' else ""}
                {"<li>모든 보고서 및 데이터 조회</li><li>속성 및 보기 설정 변경</li><li>사용자 관리 및 권한 부여</li><li>계정 설정 관리</li>" if role == 'admin' else ""}
            </ul>
        </div>
        """
        
        footer = cls._get_footer_template()
        html_content = cls._get_base_template().format(
            header=header, content=content, footer=footer
        )
        
        text_content = f"""
GA4 권한 연장 승인 완료

안녕하세요! GA4 권한이 성공적으로 연장되었습니다.

연장된 권한 정보:
사용자: {user_email}
프로퍼티: {property_name}
권한 레벨: {role_korean}
연장 승인 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
{"이전 만료일: " + str(previous_expiry) if previous_expiry else ""}
새 만료일: {expiry_date if expiry_date else '미설정'}

연장 완료:
귀하의 GA4 권한이 성공적으로 연장되었습니다. 계속해서 GA4 서비스를 이용하실 수 있습니다.

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content