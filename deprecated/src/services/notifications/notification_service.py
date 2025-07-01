#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 알림 서비스 - 일원화된 버전
========================================

모든 이메일 알림을 처리하는 통합 서비스
enum 매핑 과정 없이 직접 값을 사용하여 복잡성을 제거합니다.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from src.core.logger import get_ga4_logger
from src.core.gmail_service import GmailOAuthSender
from src.infrastructure.database import db_manager
from .email_templates import EmailTemplateManager
from .notification_types import NotificationType, NotificationUnifiedManager
from .notification_config import NotificationConfigManager
from .notification_logger import NotificationLogger

logger = get_ga4_logger()


class NotificationService:
    """통합 알림 서비스 - enum 일원화 버전"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.config_manager = NotificationConfigManager()
        self.notification_logger = NotificationLogger()
        self.gmail_sender = GmailOAuthSender()
        self.email_templates = EmailTemplateManager()
        self.logger = logger

    async def send_welcome_notification(self, user_data: Dict[str, Any]) -> bool:
        """환영 알림 발송"""
        try:
            return await self._send_notification(
                NotificationType.WELCOME, 
                user_data, 
                user_data.get('등록_계정') or user_data.get('user_email')
            )
        except Exception as e:
            self.logger.error(f"❌ 환영 알림 발송 실패: {e}")
            return False

    async def send_expiry_warning(self, user_data: Dict[str, Any], days_before: int) -> bool:
        """만료 경고 알림 발송"""
        try:
            # 일수에 따른 알림 타입 결정 (통합 매니저 사용)
            notification_type = self._get_expiry_notification_type(days_before)
            
            return await self._send_notification(
                notification_type, 
                user_data, 
                user_data.get('user_email') or user_data.get('등록_계정')
            )
        except Exception as e:
            self.logger.error(f"❌ 만료 경고 알림 발송 실패: {e}")
            return False

    async def send_deletion_notice(self, user_data: Dict[str, Any]) -> bool:
        """권한 삭제 알림 발송"""
        try:
            return await self._send_notification(
                NotificationType.EXPIRED, 
                user_data, 
                user_data.get('user_email') or user_data.get('등록_계정')
            )
        except Exception as e:
            self.logger.error(f"❌ 삭제 알림 발송 실패: {e}")
            return False

    async def send_admin_notification(self, subject: str, message: str, 
                                    details: str = None) -> bool:
        """관리자 알림 발송"""
        try:
            # 관리자 이메일 목록 조회
            admin_emails = self.config_manager.get_admin_emails_for_notification(
                NotificationType.ADMIN_NOTIFICATION
            )
            
            if not admin_emails:
                self.logger.warning("⚠ 관리자 이메일 목록이 비어있음")
                return False

            # 알림 데이터 구성
            admin_data = {
                'subject': subject,
                'message': message,
                'details': details or '',
                'timestamp': datetime.now().isoformat()
            }

            # 모든 관리자에게 발송
            success_count = 0
            for admin_email in admin_emails:
                success = await self._send_notification(
                    NotificationType.ADMIN_NOTIFICATION, 
                    admin_data, 
                    admin_email
                )
                if success:
                    success_count += 1

            self.logger.info(f"📧 관리자 알림 발송 완료: {success_count}/{len(admin_emails)}")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"❌ 관리자 알림 발송 실패: {e}")
            return False

    async def send_editor_downgrade_notification(self, user_data: Dict[str, Any]) -> bool:
        """에디터 권한 자동 다운그레이드 알림"""
        try:
            return await self._send_notification(
                NotificationType.EDITOR_AUTO_DOWNGRADE, 
                user_data, 
                user_data.get('user_email') or user_data.get('등록_계정')
            )
        except Exception as e:
            self.logger.error(f"❌ 에디터 다운그레이드 알림 실패: {e}")
            return False

    async def send_extension_approved_notification(self, user_data: Dict[str, Any]) -> bool:
        """권한 연장 승인 알림"""
        try:
            return await self._send_notification(
                NotificationType.EXTENSION_APPROVED, 
                user_data, 
                user_data.get('user_email') or user_data.get('등록_계정')
            )
        except Exception as e:
            self.logger.error(f"❌ 연장 승인 알림 실패: {e}")
            return False

    async def send_editor_approved_notification(self, user_data: Dict[str, Any]) -> bool:
        """에디터 권한 승인 알림"""
        try:
            return await self._send_notification(
                NotificationType.EDITOR_APPROVED, 
                user_data, 
                user_data.get('user_email') or user_data.get('등록_계정')
            )
        except Exception as e:
            self.logger.error(f"❌ 에디터 승인 알림 실패: {e}")
            return False

    async def send_admin_approved_notification(self, user_data: Dict[str, Any]) -> bool:
        """관리자 권한 승인 알림"""
        try:
            return await self._send_notification(
                NotificationType.ADMIN_APPROVED, 
                user_data, 
                user_data.get('user_email') or user_data.get('등록_계정')
            )
        except Exception as e:
            self.logger.error(f"❌ 관리자 승인 알림 실패: {e}")
            return False

    async def send_pending_approval_notification(self, user_data: Dict[str, Any]) -> bool:
        """즉시 승인 필요 알림 (관리자용)"""
        try:
            # 관리자들에게 발송
            admin_emails = self.config_manager.get_admin_emails_for_notification(
                NotificationType.IMMEDIATE_APPROVAL
            )
            
            success_count = 0
            for admin_email in admin_emails:
                success = await self._send_notification(
                    NotificationType.IMMEDIATE_APPROVAL, 
                    user_data, 
                    admin_email
                )
                if success:
                    success_count += 1

            return success_count > 0

        except Exception as e:
            self.logger.error(f"❌ 즉시 승인 알림 실패: {e}")
            return False

    async def send_user_pending_approval_notification(self, user_data: Dict[str, Any]) -> bool:
        """사용자에게 승인 대기 알림 발송"""
        try:
            user_email = user_data.get('user_email') or user_data.get('등록_계정')
            if not user_email:
                self.logger.error("❌ 사용자 이메일이 없습니다")
                return False
            
            self.logger.info(f"🔄 사용자 승인 대기 알림 발송 시작: {user_email}")
            
            # 승인 대기 알림 데이터 준비
            notification_data = {
                'user_email': user_email,
                'property_name': user_data.get('property_name', '알 수 없는 프로퍼티'),
                'property_id': user_data.get('property_id'),
                'role': user_data.get('role', '알 수 없음'),
                'applicant': user_data.get('applicant', user_email),
                'notification_type': user_data.get('notification_type', '승인 대기'),
                'registration_id': user_data.get('registration_id'),
                'submitted_at': datetime.now().isoformat()
            }
            
            # 사용자에게 승인 대기 알림 발송
            success = await self._send_notification(
                NotificationType.PENDING_APPROVAL,
                notification_data,
                user_email
            )
            
            if success:
                self.logger.info(f"✅ 사용자 승인 대기 알림 발송 성공: {user_email}")
            else:
                self.logger.error(f"❌ 사용자 승인 대기 알림 발송 실패: {user_email}")
            
            return success

        except Exception as e:
            self.logger.error(f"❌ 사용자 승인 대기 알림 실패: {e}")
            return False

    async def send_test_notification(self, email: str, notification_type: str = "welcome") -> bool:
        """테스트 알림 발송 (enum 안전 변환 포함)"""
        try:
            # 문자열을 enum으로 안전하게 변환
            enum_type = NotificationUnifiedManager.from_string(notification_type)
            if not enum_type:
                enum_type = NotificationType.TEST  # 기본값

            test_data = {
                'user_email': email,
                'test_timestamp': datetime.now().isoformat(),
                'notification_type': notification_type
            }

            return await self._send_notification(enum_type, test_data, email)

        except Exception as e:
            self.logger.error(f"❌ 테스트 알림 발송 실패: {e}")
            return False

    def _generate_rich_email_content(self, notification_type: NotificationType, 
                                   data: Dict[str, Any]) -> tuple[str, str, str]:
        """리치 이메일 콘텐츠 생성 (통합 버전)"""
        try:
            # enum 값을 안전하게 가져오기
            type_value = NotificationUnifiedManager.get_enum_value(notification_type)
            self.logger.info(f"🔄 리치 이메일 생성 시작: {type_value}")
            
            # 알림 타입별 템플릿 선택
            if notification_type == NotificationType.WELCOME:
                subject, text_body, html_body = self.email_templates.create_welcome_email(data)
                
            elif notification_type == NotificationType.PENDING_APPROVAL:
                subject, text_body, html_body = self.email_templates.create_pending_approval_email(data)
                
            elif notification_type in NotificationUnifiedManager.get_expiry_warning_types():
                days = NotificationUnifiedManager.get_trigger_days(notification_type)
                # days_left 값을 data에 추가
                data_with_days = data.copy()
                data_with_days['days_left'] = days
                subject, text_body, html_body = self.email_templates.create_expiry_warning_email(data_with_days)
                
            elif notification_type == NotificationType.EXPIRED:
                subject, text_body, html_body = self.email_templates.create_deletion_notice_email(data)
                
            elif notification_type == NotificationType.EXTENSION_APPROVED:
                subject, text_body, html_body = self.email_templates.create_extension_approved_email(data)
                
            elif notification_type == NotificationType.EDITOR_APPROVED:
                subject, text_body, html_body = self.email_templates.create_editor_approved_email(data)
                
            elif notification_type == NotificationType.ADMIN_APPROVED:
                subject, text_body, html_body = self.email_templates.create_admin_approved_email(data)
                
            elif notification_type == NotificationType.EDITOR_AUTO_DOWNGRADE:
                subject, text_body, html_body = self.email_templates.create_editor_downgrade_email(data)
                
            elif notification_type in NotificationUnifiedManager.get_admin_notification_types():
                subject, text_body, html_body = self.email_templates.create_admin_notification_email(
                    subject=data.get('subject', '🔧 GA4 시스템 알림'),
                    message=data.get('message', '시스템 알림'),
                    details=data.get('details')
                )
                
            elif notification_type == NotificationType.TEST:
                subject, text_body, html_body = self.email_templates.create_test_email(data)
                
            else:
                # 기본 템플릿
                subject = f"GA4 권한 관리 알림 - {type_value}"
                html_body = f"<p>GA4 권한 관리 시스템에서 알림을 보냅니다.</p><p>타입: {type_value}</p>"
                text_body = f"GA4 권한 관리 시스템에서 알림을 보냅니다.\n타입: {type_value}"

            self.logger.info(f"✅ 리치 이메일 생성 완료: {type_value}")
            return subject, html_body, text_body

        except Exception as e:
            self.logger.error(f"❌ 리치 이메일 생성 실패: {NotificationUnifiedManager.get_enum_value(notification_type)} - {e}")
            # 오류 시 기본 내용 반환
            return "GA4 권한 관리 알림", "<p>알림 내용을 불러올 수 없습니다.</p>", "알림 내용을 불러올 수 없습니다."

    async def _send_notification(self, notification_type: NotificationType, 
                               data: Dict[str, Any], recipient_email: str) -> bool:
        """통합 알림 발송 메서드 (enum 안전 처리)"""
        try:
            type_value = NotificationUnifiedManager.get_enum_value(notification_type)
            self.logger.info(f"🔄 _send_notification 시작: {type_value} -> {recipient_email}")

            # 1. 알림 활성화 확인
            if not self.config_manager.is_notification_enabled(notification_type):
                self.logger.info(f"⏹ 알림 비활성화로 건너뜀: {type_value}")
                return False

            self.logger.info(f"✅ 알림 활성화 확인 완료: {type_value}")

            # 2. 발송 조건 확인 (만료 경고의 경우)
            if NotificationUnifiedManager.is_expiry_warning(notification_type):
                self.logger.info(f"🔍 발송 조건 확인 시작: {type_value}")
                
                trigger_days = NotificationUnifiedManager.get_trigger_days(notification_type)
                if not await self._should_send_expiry_notification(data, trigger_days):
                    self.logger.info(f"⏭ 발송 조건 불만족으로 건너뜀: {type_value}")
                    return False

            # 3. 중복 발송 체크
            if await self.notification_logger.check_notification_sent_today(recipient_email, notification_type):
                self.logger.info(f"⏭ 오늘 이미 발송함으로 건너뜀: {recipient_email} - {type_value}")
                return False

            # 4. 이메일 콘텐츠 생성
            self.logger.info(f"🎨 리치 이메일 생성 시작: {type_value}")
            subject, html_body, text_body = self._generate_rich_email_content(notification_type, data)

            # 5. 이메일 발송
            success = await self.gmail_sender.send_rich_email(
                recipient_email=recipient_email,
                subject=subject,
                text_content=text_body,
                html_content=html_body
            )

            # 6. 로그 기록
            if success:
                await self.notification_logger.log_notification(
                    user_email=recipient_email,
                    notification_type=type_value,
                    sent_to=recipient_email,
                    message_subject=subject,
                    message_body=text_body,
                    status='sent',
                    property_name=data.get('property_name', ''),
                    user_registration_id=data.get('user_registration_id')
                )
                self.logger.info(f"✅ 알림 발송 성공: {recipient_email} - {type_value}")
            else:
                await self.notification_logger.log_notification(
                    user_email=recipient_email,
                    notification_type=type_value,
                    sent_to=recipient_email,
                    message_subject=subject,
                    message_body=text_body,
                    status='failed',
                    property_name=data.get('property_name', ''),
                    user_registration_id=data.get('user_registration_id')
                )
                self.logger.error(f"❌ 알림 발송 실패: {recipient_email} - {type_value}")

            return success

        except Exception as e:
            type_value = NotificationUnifiedManager.get_enum_value(notification_type)
            self.logger.error(f"❌ 알림 발송 처리 실패: {recipient_email} - {type_value} - {e}")
            return False

    def _get_expiry_notification_type(self, days_before: int) -> NotificationType:
        """일수에 따른 만료 알림 타입 반환 (통합 버전)"""
        if days_before == 30:
            return NotificationType.EXPIRY_WARNING_30
        elif days_before == 7:
            return NotificationType.EXPIRY_WARNING_7
        elif days_before == 1:
            return NotificationType.EXPIRY_WARNING_1
        elif days_before == 0:
            return NotificationType.EXPIRY_WARNING_TODAY
        else:
            return NotificationType.EXPIRY_WARNING_7  # 기본값

    async def _should_send_expiry_notification(self, user_data: Dict[str, Any], days_before: int) -> bool:
        """만료 알림 발송 조건 확인"""
        try:
            expiry_date_str = user_data.get('expiry_date') or user_data.get('종료일')
            if not expiry_date_str:
                return False

            # 날짜 파싱
            if isinstance(expiry_date_str, str):
                try:
                    expiry_date = datetime.strptime(expiry_date_str.split()[0], '%Y-%m-%d').date()
                except ValueError:
                    try:
                        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        self.logger.error(f"❌ 날짜 파싱 실패: {expiry_date_str}")
                        return False
            else:
                expiry_date = expiry_date_str

            # 발송 조건 확인
            today = datetime.now().date()
            target_date = expiry_date - timedelta(days=days_before)

            should_send = target_date == today
            if should_send:
                self.logger.info(f"✅ 발송 조건 만족: 만료일({expiry_date}) - {days_before}일 = 오늘({today})")
            else:
                self.logger.info(f"⏭ 발송 조건 불만족: 만료일({expiry_date}) - {days_before}일 = {target_date} ≠ 오늘({today})")

            return should_send

        except Exception as e:
            self.logger.error(f"❌ 만료 알림 발송 조건 확인 실패: {e}")
            return False

    async def process_expiry_notifications(self) -> Dict[str, Any]:
        """만료 알림 일괄 처리 (통합 버전)"""
        try:
            self.logger.info("🔄 만료 알림 처리 시작...")
            
            results = {
                'expiry_warnings': await self._process_expiry_warnings(),
                'deletion_notices': await self._process_deletion_notices()
            }
            
            self.logger.info("✅ 만료 알림 처리 완료")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 만료 알림 처리 실패: {e}")
            return {'error': str(e)}

    async def check_and_send_daily_notifications(self) -> Dict[str, Any]:
        """일일 알림 확인 및 발송 (통합 버전)"""
        try:
            self.logger.info("🔄 일일 알림 처리 시작...")
            
            results = {
                'expiry_warnings': await self._process_expiry_warnings(),
                'deletion_notices': await self._process_deletion_notices(), 
                'daily_summary': await self._process_daily_summary()
            }
            
            self.logger.info("✅ 일일 알림 처리 완료")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 일일 알림 처리 실패: {e}")
            return {'error': str(e)}

    async def _process_expiry_warnings(self) -> Dict[str, Any]:
        """만료 경고 알림 일괄 처리"""
        try:
            results = {'type': 'expiry_warnings', 'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
            
            # 알림 설정에서 발송 조건 확인
            trigger_days_str = await self.config_manager.get_trigger_days('expiry_warning')
            if not trigger_days_str:
                return results
            
            # 발송 일수 파싱
            trigger_days_list = await self.config_manager.parse_trigger_days(trigger_days_str)
            
            for days_before in trigger_days_list:
                # 해당 일수에 만료되는 사용자들 조회
                target_date = (datetime.now() + timedelta(days=days_before)).strftime('%Y-%m-%d')
                
                users = await self.db_manager.execute_query(
                    """
                    SELECT ur.등록_계정 as user_email, p.property_display_name as property_name, 
                           ur.property_id, ur.권한 as role, ur.종료일 as expiry_date
                    FROM user_registrations ur
                    JOIN ga4_properties p ON ur.property_id = p.property_id
                    WHERE ur.status = 'active' 
                    AND DATE(ur.종료일) = DATE(?)
                    """,
                    (target_date,)
                )
                
                for user in users:
                    results['processed'] += 1
                    
                    success = await self.send_expiry_warning(user, days_before)
                    if success:
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 만료 경고 알림 처리 실패: {e}")
            return {'type': 'expiry_warnings', 'error': str(e)}
    
    async def _process_deletion_notices(self) -> Dict[str, Any]:
        """만료된 권한 삭제 알림 처리 (실제 삭제 액션이 발생한 경우에만)"""
        try:
            results = {'type': 'deletion_notices', 'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
            
            # 실제로 삭제된 사용자들 조회 (status가 'deleted'로 변경된 경우)
            # 오늘 삭제된 사용자만 대상
            deleted_users = await self.db_manager.execute_query(
                """
                SELECT ur.등록_계정 as user_email, p.property_display_name as property_name, 
                       ur.권한 as role, ur.status, ur.종료일
                FROM user_registrations ur
                JOIN ga4_properties p ON ur.property_id = p.property_id
                WHERE ur.status = 'deleted' 
                AND DATE(ur.updated_at) = DATE('now')
                """
            )
            
            for user in deleted_users:
                results['processed'] += 1
                
                # 오늘 이미 삭제 알림을 보냈는지 확인
                email = user['user_email']
                if await self.notification_logger.check_notification_sent_today(email, NotificationType.EXPIRED):
                    self.logger.info(f"⏭ 삭제 알림 이미 발송됨: {email}")
                    results['skipped'] += 1
                    continue
                
                # 삭제 알림 발송 (우선순위 발송으로 중복 체크 우회)
                success = await self._send_notification_priority(
                    NotificationType.EXPIRED.value, 
                    email, 
                    user['property_name'], 
                    user['role'], 
                    bypass_duplicate_check=True
                )
                
                if success:
                    results['sent'] += 1
                    self.logger.info(f"📧 삭제 알림 발송 완료: {email}")
                else:
                    results['failed'] += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 삭제 알림 처리 실패: {e}")
            return {'type': 'deletion_notices', 'error': str(e)}

    async def send_deletion_notice_for_expired_users(self) -> Dict[str, Any]:
        """만료된 사용자 삭제 시 알림 발송 (실제 삭제 시점에 호출)"""
        try:
            results = {'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
            
            # 만료되었지만 아직 삭제되지 않은 사용자들 조회
            expired_users = await self.db_manager.execute_query(
                """
                SELECT ur.등록_계정 as user_email, p.property_display_name as property_name, 
                       ur.property_id, ur.권한 as role, ur.종료일 as expiry_date
                FROM user_registrations ur
                JOIN ga4_properties p ON ur.property_id = p.property_id
                WHERE ur.status = 'active' 
                AND DATE(ur.종료일) < DATE('now')
                """
            )
            
            for user in expired_users:
                results['processed'] += 1
                email = user['user_email']
                
                try:
                    # 1. 권한 삭제 처리 (status를 'deleted'로 변경)
                    await self.db_manager.execute_update(
                        """
                        UPDATE user_registrations 
                        SET status = 'deleted', updated_at = CURRENT_TIMESTAMP 
                        WHERE 등록_계정 = ? AND status = 'active'
                        """,
                        (email,)
                    )
                    
                    # 2. 삭제 알림 발송 (우선순위 발송)
                    success = await self._send_notification_priority(
                        NotificationType.EXPIRED.value, 
                        email, 
                        user['property_name'], 
                        user['role'], 
                        bypass_duplicate_check=True
                    )
                    
                    if success:
                        results['sent'] += 1
                        self.logger.info(f"🗑️ 사용자 삭제 및 알림 발송 완료: {email}")
                    else:
                        results['failed'] += 1
                        self.logger.error(f"❌ 삭제 알림 발송 실패: {email}")
                        
                except Exception as e:
                    results['failed'] += 1
                    self.logger.error(f"❌ 사용자 삭제 처리 실패 ({email}): {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 만료 사용자 삭제 처리 실패: {e}")
            return {'error': str(e)}
    
    async def _process_daily_summary(self) -> Dict[str, Any]:
        """일일 요약 알림 처리"""
        try:
            results = {'type': 'daily_summary', 'processed': 1, 'sent': 0, 'failed': 0, 'skipped': 0}
            
            # 통계 수집
            stats = await self.notification_logger.get_notification_stats()
            
            # 관리자들에게 일일 요약 발송
            summary_message = f"""
GA4 권한 관리 일일 요약:
- 오늘 발송된 알림: {stats['today_sent']}개
- 총 발송된 알림: {stats['total_sent']}개
- 실패한 알림: {stats['total_failed']}개
- 대기 중인 알림: {stats['pending_notifications']}개
- 성공률: {stats['success_rate']}%
            """
            
            success = await self.send_admin_notification(
                "[GA4 일일 요약] 권한 관리 현황",
                summary_message
            )
            
            if success:
                results['sent'] = 1
            else:
                results['failed'] = 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 일일 요약 처리 실패: {e}")
            return {'type': 'daily_summary', 'error': str(e)}

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """오래된 로그 정리 (유지보수용)"""
        return await self.notification_logger.cleanup_old_logs(days_to_keep)
    
    async def initialize_system(self) -> bool:
        """알림 시스템 초기화"""
        try:
            # 기본 알림 설정 초기화
            await self.config_manager.initialize_notification_settings()
            
            self.logger.info("✅ 알림 시스템 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 알림 시스템 초기화 실패: {e}")
            return False

    async def _send_notification_priority(self, notification_type: str, recipient_email: str, 
                                        property_name: str, role: str, 
                                        priority: int = 1, **kwargs) -> bool:
        """우선순위가 있는 알림 발송
        
        Args:
            notification_type: 알림 타입
            recipient_email: 수신자 이메일
            property_name: 프로퍼티 이름
            role: 권한 역할
            priority: 우선순위 (1=높음, 2=보통, 3=낮음)
            **kwargs: 추가 데이터
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            logger.info(f"🔄 우선순위 알림 발송 시작: {notification_type} -> {recipient_email} (우선순위: {priority})")
            
            # 우선순위에 따른 제목 접두어
            priority_prefixes = {
                1: "🚨 [긴급]",
                2: "⚠️ [중요]", 
                3: "📢 [알림]"
            }
            
            prefix = priority_prefixes.get(priority, "📢")
            
            # 삭제 알림인 경우 특별 처리
            if notification_type == "expired":
                return await self._send_deletion_notification(
                    recipient_email, property_name, role, prefix
                )
            
            # 기본 알림 처리
            unified_manager = NotificationUnifiedManager()
            subject, text_content, html_content = unified_manager.create_rich_email(
                notification_type=notification_type,
                user_email=recipient_email,
                property_name=property_name,
                role=role,
                **kwargs
            )
            
            # 우선순위 접두어 추가
            subject = f"{prefix} {subject}"
            
            # 이메일 발송
            success = await self.gmail_sender.send_rich_email(
                recipient_email=recipient_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
            if success:
                logger.info(f"✅ 우선순위 알림 발송 성공: {recipient_email} - {notification_type}")
                
                # 알림 로그 기록
                await self.notification_logger.log_notification(
                    user_email=recipient_email,
                    notification_type=notification_type,
                    property_name=property_name,
                    sent_to=recipient_email,
                    message_subject=subject,
                    message_body=text_content[:1000],  # 처음 1000자만 저장
                    status='sent'
                )
            else:
                logger.error(f"❌ 우선순위 알림 발송 실패: {recipient_email} - {notification_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 우선순위 알림 처리 실패: {recipient_email} - {notification_type} - {str(e)}")
            return False
    
    async def _send_deletion_notification(self, recipient_email: str, property_name: str, 
                                        role: str, prefix: str = "🔒") -> bool:
        """삭제 알림 발송
        
        Args:
            recipient_email: 수신자 이메일
            property_name: 프로퍼티 이름
            role: 권한 역할
            prefix: 제목 접두어
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            logger.info(f"🔄 삭제 알림 발송 시작: {recipient_email}")
            
            # EmailTemplates를 사용한 삭제 알림 생성
            data = {
                'user_email': recipient_email,
                'property_name': property_name,
                'permission_level': role,
                'expiry_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'applicant': recipient_email  # 기본값으로 사용자 이메일 사용
            }
            
            email_result = self.email_templates.expired_email(data)
            
            subject = f"{prefix} {email_result['subject']}"
            html_content = email_result['html']
            text_content = email_result['text']
            
            # 이메일 발송
            success = await self.gmail_sender.send_rich_email(
                recipient_email=recipient_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
            if success:
                logger.info(f"✅ 삭제 알림 발송 성공: {recipient_email}")
                
                # 알림 로그 기록
                await self.notification_logger.log_notification(
                    user_email=recipient_email,
                    notification_type="expired",
                    property_name=property_name,
                    sent_to=recipient_email,
                    message_subject=subject,
                    message_body=text_content[:1000],
                    status='sent'
                )
            else:
                logger.error(f"❌ 삭제 알림 발송 실패: {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 삭제 알림 처리 실패: {recipient_email} - {str(e)}")

# 싱글톤 인스턴스 생성
notification_service = NotificationService() 