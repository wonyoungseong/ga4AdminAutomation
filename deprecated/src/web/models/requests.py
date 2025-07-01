"""
API 요청 모델 정의
=================

FastAPI 요청에 사용되는 Pydantic 모델들을 정의합니다.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime


class UserRegistrationRequest(BaseModel):
    """사용자 등록 요청 모델"""
    신청자: str
    등록_계정_목록: str
    property_ids: List[str]
    권한: str
    
    @validator('권한')
    def validate_permission(cls, v):
        if v not in ['viewer', 'analyst', 'editor']:
            raise ValueError('권한은 viewer, analyst, editor 중 하나여야 합니다')
        return v


class AdminSettingsRequest(BaseModel):
    """관리자 설정 요청 모델"""
    setting_key: str
    setting_value: str


class ValidityPeriodRequest(BaseModel):
    """유효기간 설정 요청 모델"""
    role: str
    period_days: int
    description: Optional[str] = None
    is_active: bool = True


class ResponsiblePersonRequest(BaseModel):
    """담당자 설정 요청 모델"""
    name: str
    email: EmailStr
    account_id: Optional[str] = None
    property_id: Optional[str] = None
    role: str
    notification_enabled: bool = True
    is_active: bool = True


class NotificationTestRequest(BaseModel):
    """테스트 알림 요청 모델"""
    email: EmailStr
    type: str = "welcome"


class UserFilterRequest(BaseModel):
    """사용자 필터 요청 모델"""
    status: Optional[str] = None
    role: Optional[str] = None
    account_id: Optional[str] = None
    property_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    per_page: int = 50 