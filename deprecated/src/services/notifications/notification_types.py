#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 타입 정의 - 일원화된 버전
============================

GA4 권한 관리 시스템의 모든 알림 타입을 데이터베이스와 완전히 일치시켜 정의합니다.
매핑 과정 없이 동일한 값을 사용하여 복잡성을 제거합니다.
"""

from enum import Enum
from typing import Dict, List, Optional


class NotificationType(Enum):
    """알림 타입 enum - 데이터베이스 값과 완전 일치
    
    데이터베이스 CHECK 제약 조건과 정확히 일치하는 값들을 사용합니다.
    매핑 과정 없이 enum.value를 직접 데이터베이스에 저장합니다.
    """
    
    # 기본 알림들 (데이터베이스와 완전 일치)
    WELCOME = "welcome"
    TEST = "test"
    
    # 만료 경고 알림들 (기존 호환성 유지)
    EXPIRY_WARNING_30 = "30_days"
    EXPIRY_WARNING_7 = "7_days" 
    EXPIRY_WARNING_1 = "1_day"
    EXPIRY_WARNING_TODAY = "today"
    
    # 만료/삭제 알림
    EXPIRED = "expired"
    
    # 승인 관련 알림들
    PENDING_APPROVAL = "pending_approval"
    EXTENSION_APPROVED = "extension_approved"
    EDITOR_APPROVED = "editor_approved"
    ADMIN_APPROVED = "admin_approved"
    
    # 권한 변경 알림들
    EDITOR_AUTO_DOWNGRADE = "editor_auto_downgrade"
    
    # 관리자 알림들
    ADMIN_NOTIFICATION = "admin_notification"
    IMMEDIATE_APPROVAL = "immediate_approval"
    DAILY_SUMMARY = "daily_summary"


class NotificationUnifiedManager:
    """통합 알림 관리자 - 모든 알림 관련 로직을 단일 클래스로 통합
    
    매핑 과정 없이 enum 값을 직접 사용하여 복잡성을 제거합니다.
    """
    
    @classmethod
    def get_enum_value(cls, notification_type: NotificationType) -> str:
        """enum 값을 안전하게 반환 (매핑 없이 직접 사용)"""
        return notification_type.value
    
    @classmethod
    def get_database_value(cls, notification_type: NotificationType) -> str:
        """데이터베이스 저장용 값 반환 (enum 값과 동일)"""
        return notification_type.value
    
    @classmethod
    def get_trigger_days(cls, notification_type: NotificationType) -> int:
        """각 알림 타입의 발송 일수 반환"""
        trigger_mapping = {
            NotificationType.EXPIRY_WARNING_30: 30,
            NotificationType.EXPIRY_WARNING_7: 7,
            NotificationType.EXPIRY_WARNING_1: 1,
            NotificationType.EXPIRY_WARNING_TODAY: 0,
        }
        # 기본값은 0 (즉시 발송)
        return trigger_mapping.get(notification_type, 0)
    
    @classmethod
    def get_priority(cls, notification_type: NotificationType) -> str:
        """알림 우선순위 반환"""
        high_priority = {
            NotificationType.EXPIRY_WARNING_TODAY,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRED
        }
        medium_priority = {
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EDITOR_AUTO_DOWNGRADE,
            NotificationType.IMMEDIATE_APPROVAL,
            NotificationType.EDITOR_APPROVED,
            NotificationType.ADMIN_APPROVED,
            NotificationType.ADMIN_NOTIFICATION
        }
        
        if notification_type in high_priority:
            return "high"
        elif notification_type in medium_priority:
            return "medium"
        else:
            return "low"
    
    @classmethod
    def get_category(cls, notification_type: NotificationType) -> str:
        """알림 카테고리 반환"""
        user_notifications = {
            NotificationType.WELCOME,
            NotificationType.EXTENSION_APPROVED,
            NotificationType.EDITOR_APPROVED,
            NotificationType.ADMIN_APPROVED
        }
        warning_notifications = {
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY
        }
        admin_notifications = {
            NotificationType.ADMIN_NOTIFICATION,
            NotificationType.IMMEDIATE_APPROVAL,
            NotificationType.DAILY_SUMMARY
        }
        
        if notification_type in user_notifications:
            return "user"
        elif notification_type in warning_notifications:
            return "warning"
        elif notification_type in admin_notifications:
            return "admin"
        else:
            return "system"
    
    @classmethod
    def is_expiry_warning(cls, notification_type: NotificationType) -> bool:
        """만료 경고 알림인지 확인"""
        expiry_warnings = {
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY
        }
        return notification_type in expiry_warnings
    
    @classmethod
    def is_automated(cls, notification_type: NotificationType) -> bool:
        """자동 발송 알림인지 확인"""
        automated_types = {
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY,
            NotificationType.EDITOR_AUTO_DOWNGRADE,
            NotificationType.EXPIRED,
            NotificationType.IMMEDIATE_APPROVAL,
            NotificationType.DAILY_SUMMARY
        }
        return notification_type in automated_types
    
    @classmethod
    def get_expiry_warning_types(cls) -> List[NotificationType]:
        """만료 경고 알림 타입 목록 반환"""
        return [
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY
        ]
    
    @classmethod
    def get_admin_notification_types(cls) -> List[NotificationType]:
        """관리자 알림 타입 목록 반환"""
        return [
            NotificationType.ADMIN_NOTIFICATION,
            NotificationType.IMMEDIATE_APPROVAL,
            NotificationType.DAILY_SUMMARY
        ]
    
    @classmethod
    def from_string(cls, value: str) -> Optional[NotificationType]:
        """문자열에서 enum 찾기 (안전한 변환)"""
        for notification_type in NotificationType:
            if notification_type.value == value:
                return notification_type
        return None
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """모든 알림 타입 값 목록 반환 (DB CHECK 제약 조건용)"""
        return [nt.value for nt in NotificationType]


# 하위 호환성을 위한 별칭들
NotificationMetadata = NotificationUnifiedManager 