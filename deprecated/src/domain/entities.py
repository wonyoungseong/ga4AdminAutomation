#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Entities
===============

GA4 권한 관리 시스템의 도메인 엔티티들을 정의합니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4

# 통합된 NotificationType import
from ..services.notifications.notification_types import NotificationType


class PermissionLevel(Enum):
    """권한 레벨"""
    ANALYST = "analyst"
    EDITOR = "editor"
    ADMIN = "admin"


class RegistrationStatus(Enum):
    """등록 상태"""
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    EXPIRED = "expired"
    DELETED = "deleted"
    REJECTED = "rejected"


@dataclass
class GA4Account:
    """GA4 계정 엔티티"""
    account_id: str
    account_display_name: str
    최초_확인일: datetime
    최근_업데이트일: datetime
    삭제여부: bool = False
    현재_존재여부: bool = True
    service_account_access: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_last_checked(self) -> None:
        """최근 업데이트일 갱신"""
        self.최근_업데이트일 = datetime.now()
        self.updated_at = datetime.now()

    def mark_as_deleted(self) -> None:
        """삭제 표시"""
        self.삭제여부 = True
        self.현재_존재여부 = False
        self.update_last_checked()

    def mark_as_existing(self) -> None:
        """존재 표시"""
        self.삭제여부 = False
        self.현재_존재여부 = True
        self.update_last_checked()


@dataclass
class GA4Property:
    """GA4 프로퍼티 엔티티"""
    property_id: str
    account_id: str
    property_display_name: str
    property_type: str
    최초_확인일: datetime
    최근_업데이트일: datetime
    삭제여부: bool = False
    현재_존재여부: bool = True
    등록_가능여부: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_last_checked(self) -> None:
        """최근 업데이트일 갱신"""
        self.최근_업데이트일 = datetime.now()
        self.updated_at = datetime.now()

    def mark_as_deleted(self) -> None:
        """삭제 표시"""
        self.삭제여부 = True
        self.현재_존재여부 = False
        self.등록_가능여부 = False
        self.update_last_checked()

    def mark_as_existing(self) -> None:
        """존재 표시"""
        self.삭제여부 = False
        self.현재_존재여부 = True
        self.등록_가능여부 = True
        self.update_last_checked()

    def disable_registration(self) -> None:
        """등록 비활성화"""
        self.등록_가능여부 = False
        self.update_last_checked()


@dataclass
class UserRegistration:
    """사용자 등록 엔티티"""
    신청자: str
    등록_계정: str
    property_id: str
    권한: PermissionLevel
    신청일: datetime
    종료일: datetime
    id: Optional[int] = None
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    approval_required: bool = False
    연장_횟수: int = 0
    최근_연장일: Optional[datetime] = None
    binding_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """초기화 후 처리"""
        # Editor 권한은 수동 승인 필요
        if self.권한 == PermissionLevel.EDITOR:
            self.approval_required = True
            self.status = RegistrationStatus.PENDING_APPROVAL

    @property
    def days_until_expiry(self) -> int:
        """만료까지 남은 일수"""
        delta = self.종료일 - datetime.now()
        return max(0, delta.days)

    @property
    def is_expired(self) -> bool:
        """만료 여부"""
        return datetime.now() > self.종료일

    @property
    def needs_notification(self) -> bool:
        """알림 필요 여부 (30, 7, 1일 전, 당일)"""
        days_left = self.days_until_expiry
        return days_left in [30, 7, 1, 0] or self.is_expired

    def extend_permission(self, extension_days: int = 30) -> None:
        """권한 연장"""
        from datetime import timedelta
        
        self.종료일 += timedelta(days=extension_days)
        self.연장_횟수 += 1
        self.최근_연장일 = datetime.now()
        self.updated_at = datetime.now()

    def approve(self) -> None:
        """승인 처리"""
        if self.status == RegistrationStatus.PENDING_APPROVAL:
            self.status = RegistrationStatus.ACTIVE
            self.approval_required = False
            self.updated_at = datetime.now()

    def reject(self) -> None:
        """거부 처리"""
        if self.status == RegistrationStatus.PENDING_APPROVAL:
            self.status = RegistrationStatus.REJECTED
            self.updated_at = datetime.now()

    def expire(self) -> None:
        """만료 처리"""
        self.status = RegistrationStatus.EXPIRED
        self.updated_at = datetime.now()

    def delete(self) -> None:
        """삭제 처리"""
        self.status = RegistrationStatus.DELETED
        self.updated_at = datetime.now()

    @property
    def permission_display_name(self) -> str:
        """권한 표시명"""
        mapping = {
            PermissionLevel.ANALYST: "Analyst",
            PermissionLevel.EDITOR: "Editor",
            PermissionLevel.ADMIN: "Admin"
        }
        return mapping.get(self.권한, str(self.권한.value))

    @property
    def status_display_name(self) -> str:
        """상태 표시명"""
        mapping = {
            RegistrationStatus.PENDING_APPROVAL: "승인 대기",
            RegistrationStatus.ACTIVE: "활성",
            RegistrationStatus.EXPIRED: "만료",
            RegistrationStatus.DELETED: "삭제",
            RegistrationStatus.REJECTED: "거부"
        }
        return mapping.get(self.status, str(self.status.value))


@dataclass
class NotificationLog:
    """알림 로그 엔티티"""
    id: Optional[int] = None
    user_registration_id: Optional[int] = None
    user_email: str = ""
    notification_type: NotificationType = NotificationType.WELCOME
    property_id: Optional[str] = None
    sent_to: str = ""
    sent_at: Optional[datetime] = None
    message_subject: str = ""
    message_body: str = ""
    status: str = "sent"
    response_received: bool = False
    response_content: Optional[str] = None
    
    def __post_init__(self):
        if self.sent_at is None:
            self.sent_at = datetime.now(timezone.utc)


@dataclass
class NotificationSetting:
    """알림 설정 엔티티"""
    id: Optional[int] = None
    notification_type: str = ""  # 데이터베이스 설정 타입 (expiry_warning, expiry_notice 등)
    enabled: bool = True
    trigger_days: Optional[str] = None  # "30,7,1,0" 형태
    template_subject: Optional[str] = None
    template_body: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_trigger_days_list(self) -> List[int]:
        """trigger_days 문자열을 정수 리스트로 변환"""
        if not self.trigger_days:
            return []
        return [int(day.strip()) for day in self.trigger_days.split(",") if day.strip().isdigit()]
    
    def has_trigger_day(self, days: int) -> bool:
        """특정 일수가 trigger_days에 포함되어 있는지 확인"""
        return days in self.get_trigger_days_list()


@dataclass
class AuditLog:
    """감사 로그 엔티티"""
    action_type: str
    target_type: str
    target_id: str
    performed_by: Optional[str]
    action_details: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    @classmethod
    def create_success_log(cls, action_type: str, target_type: str, target_id: str, 
                          action_details: str, performed_by: Optional[str] = None) -> 'AuditLog':
        """성공 로그 생성"""
        return cls(
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            action_details=action_details,
            success=True,
            performed_by=performed_by
        )

    @classmethod
    def create_failure_log(cls, action_type: str, target_type: str, target_id: str,
                          action_details: str, error_message: str, 
                          performed_by: Optional[str] = None) -> 'AuditLog':
        """실패 로그 생성"""
        return cls(
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            action_details=action_details,
            success=False,
            error_message=error_message,
            performed_by=performed_by
        ) 