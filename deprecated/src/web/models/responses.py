"""
API 응답 모델 정의
=================

FastAPI 응답에 사용되는 Pydantic 모델들을 정의합니다.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ApiResponse(BaseModel):
    """기본 API 응답 모델"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class PropertyInfo(BaseModel):
    """프로퍼티 정보 모델"""
    property_id: str
    property_name: str
    account_name: str
    time_zone: str = "Asia/Seoul"
    last_updated: Optional[str] = None


class UserRegistration(BaseModel):
    """사용자 등록 정보 모델"""
    id: int
    applicant: str
    user_email: str
    property_id: str
    property_name: Optional[str] = None
    account_name: Optional[str] = None
    permission_level: str
    status: str
    created_at: Optional[str] = None
    expiry_date: Optional[str] = None
    ga4_registered: bool = False
    extension_count: int = 0


class StatsInfo(BaseModel):
    """통계 정보 모델"""
    total_accounts: int = 0
    total_properties: int = 0
    active_users: int = 0
    expiring_soon: int = 0
    total_notifications: int = 0
    total_audit_logs: int = 0
    total_registrations: int = 0


class DashboardData(BaseModel):
    """대시보드 데이터 모델"""
    properties: List[PropertyInfo]
    registrations: List[UserRegistration]
    stats: StatsInfo
    notification_stats: Dict[str, Any]
    recent_logs: List[Dict[str, Any]]


class UserListResponse(BaseModel):
    """사용자 목록 응답 모델"""
    success: bool
    users: List[UserRegistration]
    pagination: Dict[str, Any]


class StatsResponse(BaseModel):
    """통계 응답 모델"""
    success: bool
    stats: StatsInfo


class NotificationStats(BaseModel):
    """알림 통계 모델"""
    total_sent: int = 0
    today_sent: int = 0
    pending_notifications: int = 0
    last_sent: str = "없음"


class SchedulerStatus(BaseModel):
    """스케줄러 상태 모델"""
    is_running: bool
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class ValidityPeriod(BaseModel):
    """유효기간 모델"""
    id: int
    role: str
    period_days: int
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ResponsiblePerson(BaseModel):
    """담당자 모델"""
    id: int
    name: str
    email: str
    account_id: Optional[str] = None
    property_id: Optional[str] = None
    role: str
    notification_enabled: bool = True
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None 