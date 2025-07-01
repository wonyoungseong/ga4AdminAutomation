#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 핸들러
==========

각 알림 유형별 처리 로직을 담당하는 핸들러들을 정의합니다.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.infrastructure.database import DatabaseManager
from src.services.notifications.notification_types import NotificationType, NotificationMetadata
from src.services.notifications.notification_config import NotificationConfigManager

logger = logging.getLogger(__name__)


class NotificationHandler(ABC):
    """알림 핸들러 기본 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, config_manager: NotificationConfigManager):
        self.db_manager = db_manager
        self.config_manager = config_manager
    
    @abstractmethod
    def get_notification_type(self) -> NotificationType:
        """핸들러가 처리하는 알림 타입 반환"""
        pass
    
    @abstractmethod
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """알림 발송 조건 확인"""
        pass
    
    @abstractmethod
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """메시지 제목과 내용 생성"""
        pass


class WelcomeNotificationHandler(NotificationHandler):
    """환영 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.WELCOME
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """환영 알림은 권한 승인 직후 발송"""
        try:
            # 이미 환영 알림을 발송했는지 확인
            check_query = """
            SELECT COUNT(*) as count 
            FROM notification_logs 
            WHERE user_email = ? 
            AND notification_type = ?
            AND property_id = ?
            """
            
            result = self.db_manager.execute_query_sync(
                check_query, 
                (user_data['email'], self.get_notification_type().value, user_data['property_id'])
            )
            
            if result and result[0]['count'] > 0:
                logger.info(f"⏭ 이미 환영 알림 발송됨: {user_data['email']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 환영 알림 발송 조건 확인 실패: {e}")
            return False
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """환영 메시지 생성"""
        property_name = user_data.get('property_name', '알 수 없음')
        role = user_data.get('role', 'Viewer')
        
        subject = f"[GA4 권한 부여] {property_name} 접근 권한이 성공적으로 부여되었습니다"
        
        body = f"""
안녕하세요,

{property_name} GA4 프로퍼티에 대한 {role} 권한이 성공적으로 부여되었습니다.

▶ 프로퍼티: {property_name}
▶ 부여된 권한: {role}
▶ 부여일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}

이제 GA4 콘솔에서 해당 프로퍼티의 데이터를 확인하실 수 있습니다.

감사합니다.
        """.strip()
        
        return subject, body


class ExpiryWarningHandler(NotificationHandler):
    """만료 경고 알림 핸들러"""
    
    def __init__(self, db_manager: DatabaseManager, config_manager: NotificationConfigManager, days_before: int):
        super().__init__(db_manager, config_manager)
        self.days_before = days_before
    
    def get_notification_type(self) -> NotificationType:
        """일수에 따른 알림 타입 반환"""
        if self.days_before == 30:
            return NotificationType.EXPIRY_WARNING_30
        elif self.days_before == 7:
            return NotificationType.EXPIRY_WARNING_7
        elif self.days_before == 1:
            return NotificationType.EXPIRY_WARNING_1
        elif self.days_before == 0:
            return NotificationType.EXPIRY_WARNING_TODAY
        else:
            # 기본값 
            return NotificationType.EXPIRY_WARNING_7
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """만료 경고 발송 조건 확인"""
        try:
            # 만료일 확인
            expiry_date_str = user_data.get('expiry_date')
            if not expiry_date_str:
                logger.warning(f"⚠ 만료일이 없음: {user_data.get('email', 'Unknown')}")
                return False
            
            # 문자열을 datetime으로 변환 (시간 정보 제거)
            if isinstance(expiry_date_str, str):
                try:
                    expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00')).date()
                except ValueError:
                    # ISO 형식이 아닌 경우 다른 형식 시도
                    expiry_date = datetime.strptime(expiry_date_str.split()[0], '%Y-%m-%d').date()
            else:
                expiry_date = expiry_date_str.date()
            
            # 오늘 날짜와 비교 (시간 정보 제거)
            today = datetime.now().date()
            days_until_expiry = (expiry_date - today).days
            
            logger.info(f"📅 만료일 계산: 오늘={today}, 만료={expiry_date}, 남은일수={days_until_expiry}, 대상일수={self.days_before}")
            
            # 정확히 해당 일수 전인지 확인
            if days_until_expiry != self.days_before:
                logger.info(f"⏭ 발송 조건 불만족: 남은일수({days_until_expiry}) != 대상일수({self.days_before})")
                return False
            
            # 중복 발송 방지 - 같은 날 같은 타입의 알림이 이미 발송되었는지 확인
            today_str = today.strftime('%Y-%m-%d')
            
            check_query = """
            SELECT COUNT(*) as count 
            FROM notification_logs 
            WHERE user_email = ? 
            AND notification_type = ?
            AND property_id = ?
            AND DATE(sent_at) = ?
            """
            
            result = self.db_manager.execute_query_sync(
                check_query, 
                (user_data['email'], self.get_notification_type().value, user_data['property_id'], today_str)
            )
            
            if result and result[0]['count'] > 0:
                logger.info(f"⏭ 오늘 이미 발송된 알림: {self.get_notification_type().value} for {user_data['email']}")
                return False
            
            logger.info(f"✅ 발송 조건 만족: {self.get_notification_type().value} for {user_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 만료 경고 발송 조건 확인 실패: {e}")
            return False
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """만료 경고 메시지 생성"""
        property_name = user_data.get('property_name', '알 수 없음')
        role = user_data.get('role', 'Viewer')
        expiry_date = user_data.get('expiry_date', '알 수 없음')
        
        if self.days_before == 0:
            subject = f"[GA4 권한 만료] {property_name} 권한이 오늘 만료됩니다"
            urgency = "⚠️ 긴급"
            message = "오늘 만료됩니다"
        elif self.days_before == 1:
            subject = f"[GA4 권한 만료 알림] {property_name} 권한이 내일 만료됩니다"
            urgency = "🔴 중요"
            message = "내일 만료됩니다"
        else:
            subject = f"[GA4 권한 만료 알림] {property_name} 권한이 {self.days_before}일 후 만료됩니다"
            urgency = "🟡 알림"
            message = f"{self.days_before}일 후 만료됩니다"
        
        body = f"""
{urgency}

안녕하세요,

{property_name} GA4 프로퍼티에 대한 권한이 {message}.

▶ 프로퍼티: {property_name}
▶ 현재 권한: {role}
▶ 만료일: {expiry_date}

권한 연장이 필요하시면 관리자에게 문의해 주세요.

감사합니다.
        """.strip()
        
        return subject, body


class ExpiredNotificationHandler(NotificationHandler):
    """권한 만료 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.EXPIRED
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """권한 만료 발송 조건 확인"""
        try:
            # 만료일이 오늘이거나 과거인 경우
            expiry_date_str = user_data.get('expiry_date')
            if not expiry_date_str:
                return False
            
            # 문자열을 datetime으로 변환 (시간 정보 제거)
            if isinstance(expiry_date_str, str):
                try:
                    expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00')).date()
                except ValueError:
                    expiry_date = datetime.strptime(expiry_date_str.split()[0], '%Y-%m-%d').date()
            else:
                expiry_date = expiry_date_str.date()
            
            today = datetime.now().date()
            
            # 만료일이 오늘이거나 과거인지 확인
            if expiry_date > today:
                return False
            
            # 중복 발송 방지
            check_query = """
            SELECT COUNT(*) as count 
            FROM notification_logs 
            WHERE user_email = ? 
            AND notification_type = ?
            AND property_id = ?
            """
            
            result = self.db_manager.execute_query_sync(
                check_query, 
                (user_data['email'], self.get_notification_type().value, user_data['property_id'])
            )
            
            return not (result and result[0]['count'] > 0)
            
        except Exception as e:
            logger.error(f"❌ 권한 만료 발송 조건 확인 실패: {e}")
            return False
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """권한 만료 메시지 생성"""
        property_name = user_data.get('property_name', '알 수 없음')
        role = user_data.get('role', 'Viewer')
        expiry_date = user_data.get('expiry_date', '알 수 없음')
        
        subject = f"[GA4 권한 만료] {property_name} 권한이 만료되었습니다"
        
        body = f"""
🔴 권한 만료 알림

안녕하세요,

{property_name} GA4 프로퍼티에 대한 권한이 만료되었습니다.

▶ 프로퍼티: {property_name}
▶ 이전 권한: {role}
▶ 만료일: {expiry_date}

현재 해당 프로퍼티에 대한 접근이 제한되었습니다.
권한 재신청이 필요하시면 관리자에게 문의해 주세요.

감사합니다.
        """.strip()
        
        return subject, body


class TestNotificationHandler(NotificationHandler):
    """테스트 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.TEST
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """테스트 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """테스트 메시지 생성"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        subject = f"[GA4 테스트 알림] 알림 시스템 테스트 - {timestamp}"
        
        body = f"""
🧪 테스트 알림

이 메시지는 GA4 권한 관리 시스템의 알림 기능 테스트입니다.

▶ 발송 시간: {timestamp}
▶ 수신자: {user_data.get('email', 'Unknown')}
▶ 시스템: GA4 권한 관리 시스템

이 메시지를 받으셨다면 알림 시스템이 정상적으로 작동하고 있습니다.

감사합니다.
        """.strip()
        
        return subject, body


class EditorApprovedNotificationHandler(NotificationHandler):
    """Editor 승인 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.EDITOR_APPROVED
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """Editor 승인 알림은 항상 발송 (중복 체크 우회)"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """Editor 승인 메시지 생성"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        property_name = user_data.get('property_name', '알 수 없음')
        user_email = user_data.get('email', 'Unknown')
        
        subject = f"🎉 [GA4 Editor 권한 승인] {property_name} - Editor 권한이 승인되었습니다"
        
        body = f"""
🎉 Editor 권한 승인 완료

안녕하세요, {user_email}님!

GA4 Editor 권한 신청이 승인되었습니다.

▶ 프로퍼티: {property_name}
▶ 승인된 권한: Editor (편집자)
▶ 승인 시간: {timestamp}

이제 해당 프로퍼티에서 데이터 편집 권한을 사용하실 수 있습니다.

감사합니다.
        """.strip()
        
        return subject, body


class AdminApprovedNotificationHandler(NotificationHandler):
    """Admin 승인 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.ADMIN_APPROVED
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """Admin 승인 알림은 항상 발송 (중복 체크 우회)"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """Admin 승인 메시지 생성"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        property_name = user_data.get('property_name', '알 수 없음')
        user_email = user_data.get('email', 'Unknown')
        
        subject = f"🚀 [GA4 Admin 권한 승인] {property_name} - Admin 권한이 승인되었습니다"
        
        body = f"""
🚀 Admin 권한 승인 완료

안녕하세요, {user_email}님!

GA4 Admin 권한 신청이 승인되었습니다.

▶ 프로퍼티: {property_name}
▶ 승인된 권한: Admin (관리자)
▶ 승인 시간: {timestamp}

이제 해당 프로퍼티에서 모든 관리자 권한을 사용하실 수 있습니다.

감사합니다.
        """.strip()
        
        return subject, body


class AdminNotificationHandler(NotificationHandler):
    """관리자 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.ADMIN_NOTIFICATION
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """관리자 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """관리자 알림 메시지 생성"""
        subject = f"[GA4 관리자 알림] {user_data.get('title', '중요 알림')}"
        
        message = user_data.get('message', '관리자에게 전달할 내용이 있습니다.')
        
        body = f"""
관리자님께,

{message}

시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

GA4 권한 관리 시스템
        """
        
        return subject, body


class ExtensionApprovedNotificationHandler(NotificationHandler):
    """권한 연장 승인 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.EXTENSION_APPROVED
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """권한 연장 승인 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """권한 연장 승인 메시지 생성"""
        property_name = user_data.get('property_name', '알 수 없음')
        new_expiry_date = user_data.get('new_expiry_date', '알 수 없음')
        
        subject = f"[GA4 권한 연장 승인] {property_name} 권한이 연장되었습니다"
        
        body = f"""
안녕하세요!

GA4 프로퍼티 '{property_name}'에 대한 권한 연장이 승인되었습니다.

연장 정보:
- 사용자: {user_data.get('email', '')}
- 프로퍼티: {property_name}
- 권한: {user_data.get('role', 'Viewer')}
- 새로운 만료일: {new_expiry_date}

계속해서 GA4 데이터에 접근하실 수 있습니다.

감사합니다.
GA4 권한 관리 시스템
        """
        
        return subject, body


class EditorAutoDowngradeNotificationHandler(NotificationHandler):
    """Editor 자동 다운그레이드 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.EDITOR_AUTO_DOWNGRADE
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """Editor 다운그레이드 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """Editor 다운그레이드 메시지 생성"""
        property_name = user_data.get('property_name', '알 수 없음')
        
        subject = f"[GA4 권한 변경] {property_name} Editor 권한이 Viewer로 변경되었습니다"
        
        body = f"""
안녕하세요!

GA4 프로퍼티 '{property_name}'에 대한 Editor 권한이 7일 후 자동으로 Viewer 권한으로 변경되었습니다.

변경 정보:
- 사용자: {user_data.get('email', '')}
- 프로퍼티: {property_name}
- 이전 권한: Editor
- 현재 권한: Viewer
- 변경 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

계속해서 데이터 조회는 가능하지만, 편집 권한은 제한됩니다.
Editor 권한이 필요하시면 관리자에게 재신청해주세요.

감사합니다.
GA4 권한 관리 시스템
        """
        
        return subject, body


class PendingApprovalNotificationHandler(NotificationHandler):
    """승인 대기 알림 핸들러 (사용자용)"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.PENDING_APPROVAL
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """승인 대기 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """승인 대기 메시지 생성"""
        property_name = user_data.get('property_name', '알 수 없는 프로퍼티')
        role = user_data.get('role', '알 수 없음')
        notification_type = user_data.get('notification_type', '승인 대기')
        
        subject = f"📋 [GA4 {role.upper()} 권한 신청] {property_name} - 승인 대기 중입니다"
        
        body = f"""
안녕하세요!

GA4 {role.upper()} 권한 신청이 접수되어 승인 대기 중입니다.

신청 정보:
▶ 사용자: {user_data.get('user_email', '')}
▶ 프로퍼티: {property_name}
▶ 요청 권한: {role.upper()}
▶ 신청자: {user_data.get('applicant', '알 수 없음')}
▶ 처리 유형: {notification_type}
▶ 신청 시간: {user_data.get('submitted_at', datetime.now().isoformat())}

{role.upper()} 권한은 관리자 승인이 필요한 권한입니다.
승인이 완료되면 별도 알림을 받으실 수 있습니다.

감사합니다.
GA4 권한 관리 시스템
        """
        
        return subject, body


class ImmediateApprovalNotificationHandler(NotificationHandler):
    """즉시 승인 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.IMMEDIATE_APPROVAL
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """즉시 승인 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """즉시 승인 알림 메시지 생성"""
        approval_type = user_data.get('approval_type', '권한 승인')
        
        subject = f"[GA4 즉시 승인] {approval_type} 처리 완료"
        
        body = f"""
관리자님께,

다음 승인 요청이 즉시 처리되었습니다:

승인 정보:
- 승인 유형: {approval_type}
- 사용자: {user_data.get('email', '')}
- 프로퍼티: {user_data.get('property_name', '알 수 없음')}
- 권한: {user_data.get('role', '')}
- 처리 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

GA4 권한 관리 시스템
        """
        
        return subject, body


class DailySummaryNotificationHandler(NotificationHandler):
    """일일 요약 알림 핸들러"""
    
    def get_notification_type(self) -> NotificationType:
        return NotificationType.DAILY_SUMMARY
    
    def should_send_notification(self, user_data: Dict[str, Any]) -> bool:
        """일일 요약 알림은 항상 발송"""
        return True
    
    def generate_message_content(self, user_data: Dict[str, Any]) -> tuple[str, str]:
        """일일 요약 메시지 생성"""
        today = datetime.now().strftime('%Y년 %m월 %d일')
        
        subject = f"[GA4 일일 요약] {today} 권한 관리 현황"
        
        stats = user_data.get('stats', {})
        
        body = f"""
관리자님께,

{today} GA4 권한 관리 시스템 일일 요약을 전달드립니다.

📊 오늘의 활동:
- 발송된 알림: {stats.get('today_sent', 0)}개
- 신규 등록: {stats.get('new_registrations', 0)}개
- 권한 만료: {stats.get('expired_today', 0)}개
- 권한 연장: {stats.get('extended_today', 0)}개

📈 전체 현황:
- 총 활성 사용자: {stats.get('active_users', 0)}명
- 총 발송 알림: {stats.get('total_sent', 0)}개
- 성공률: {stats.get('success_rate', 0)}%

⚠️ 주의사항:
- 만료 예정 사용자: {stats.get('expiring_soon', 0)}명
- 실패한 알림: {stats.get('failed_notifications', 0)}개

GA4 권한 관리 시스템
        """
        
        return subject, body


class NotificationHandlerFactory:
    """알림 핸들러 팩토리"""
    
    @staticmethod
    def create_handler(
        notification_type: NotificationType, 
        db_manager: DatabaseManager, 
        config_manager: NotificationConfigManager
    ) -> NotificationHandler:
        """알림 타입에 따른 핸들러 생성"""
        
        if notification_type == NotificationType.WELCOME:
            return WelcomeNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.EXPIRY_WARNING_30:
            return ExpiryWarningHandler(db_manager, config_manager, 30)
        
        elif notification_type == NotificationType.EXPIRY_WARNING_7:
            return ExpiryWarningHandler(db_manager, config_manager, 7)
        
        elif notification_type == NotificationType.EXPIRY_WARNING_1:
            return ExpiryWarningHandler(db_manager, config_manager, 1)
        
        elif notification_type == NotificationType.EXPIRY_WARNING_TODAY:
            return ExpiryWarningHandler(db_manager, config_manager, 0)
        
        elif notification_type == NotificationType.EXPIRED:
            return ExpiredNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.TEST:
            return TestNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.EDITOR_APPROVED:
            return EditorApprovedNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.ADMIN_APPROVED:
            return AdminApprovedNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.ADMIN_NOTIFICATION:
            return AdminNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.EXTENSION_APPROVED:
            return ExtensionApprovedNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.EDITOR_AUTO_DOWNGRADE:
            return EditorAutoDowngradeNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.PENDING_APPROVAL:
            return PendingApprovalNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.IMMEDIATE_APPROVAL:
            return ImmediateApprovalNotificationHandler(db_manager, config_manager)
        
        elif notification_type == NotificationType.DAILY_SUMMARY:
            return DailySummaryNotificationHandler(db_manager, config_manager)
        
        else:
            raise ValueError(f"지원하지 않는 알림 타입: {notification_type}")
    
    @staticmethod
    def get_all_expiry_warning_handlers(
        db_manager: DatabaseManager, 
        config_manager: NotificationConfigManager
    ) -> List[NotificationHandler]:
        """모든 만료 경고 핸들러 반환"""
        handlers = []
        for days in [30, 7, 1, 0]:
            handler = ExpiryWarningHandler(db_manager, config_manager, days)
            handlers.append(handler)
        return handlers 