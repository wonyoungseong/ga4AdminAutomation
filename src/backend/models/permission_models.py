"""
권한 관리 관련 Pydantic 모델들
===============================

권한 신청, 승인, 만료 관리 등에 사용되는 데이터 모델들
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class PermissionLevel(str, Enum):
    """권한 수준 열거형"""
    VIEWER = "viewer"
    ANALYST = "analyst" 
    EDITOR = "editor"
    ADMINISTRATOR = "administrator"


class PermissionStatus(str, Enum):
    """권한 상태 열거형"""
    PENDING = "pending"           # 승인 대기
    APPROVED = "approved"         # 승인됨
    ACTIVE = "active"            # 활성 상태
    REJECTED = "rejected"         # 거부됨
    EXPIRED = "expired"          # 만료됨
    REVOKED = "revoked"          # 철회됨


class PermissionRequest(BaseModel):
    """권한 신청 요청 모델"""
    property_id: str = Field(..., description="GA4 속성 ID")
    permission_level: PermissionLevel = Field(..., description="신청할 권한 수준")
    requested_duration_days: int = Field(..., ge=1, le=365, description="신청 기간 (일)")
    justification: str = Field(..., min_length=10, max_length=500, description="신청 사유")
    
    @validator('property_id')
    def validate_property_id(cls, v):
        """GA4 속성 ID 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('GA4 속성 ID는 필수입니다')
        # GA4 속성 ID는 보통 숫자로만 구성됨
        if not v.replace('-', '').isdigit():
            raise ValueError('올바른 GA4 속성 ID 형식이 아닙니다')
        return v.strip()
    
    @validator('requested_duration_days')
    def validate_duration(cls, v, values):
        """신청 기간 검증 (권한 수준별 제한)"""
        permission_level = values.get('permission_level')
        
        if permission_level in [PermissionLevel.VIEWER, PermissionLevel.ANALYST]:
            if v > 60:
                raise ValueError('Viewer/Analyst 권한은 최대 60일까지 신청 가능합니다')
        elif permission_level == PermissionLevel.EDITOR:
            if v > 7:
                raise ValueError('Editor 권한은 최대 7일까지 신청 가능합니다')
        elif permission_level == PermissionLevel.ADMINISTRATOR:
            if v > 90:
                raise ValueError('Administrator 권한은 최대 90일까지 신청 가능합니다')
        
        return v


class PermissionRequestCreate(PermissionRequest):
    """권한 신청 생성 모델 (사용자용)"""
    # 사용자는 자신의 이메일이 자동으로 설정되므로 이메일 필드 불필요
    pass


class PermissionRequestResponse(BaseModel):
    """권한 신청 응답 모델"""
    grant_id: int
    user_id: int
    user_email: str
    user_name: str
    property_id: str
    permission_level: PermissionLevel
    requested_duration_days: int
    justification: str
    status: PermissionStatus
    requested_at: datetime
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    rejected_reason: Optional[str] = None


class PermissionApprovalRequest(BaseModel):
    """권한 승인/거부 요청 모델"""
    grant_id: int = Field(..., description="권한 신청 ID")
    action: str = Field(..., pattern="^(approve|reject)$", description="승인 또는 거부")
    admin_notes: Optional[str] = Field(None, max_length=500, description="관리자 메모")
    custom_duration_days: Optional[int] = Field(None, ge=1, le=365, description="사용자 정의 기간")


class PermissionExtensionRequest(BaseModel):
    """권한 연장 요청 모델"""
    grant_id: int = Field(..., description="연장할 권한 ID")
    extension_days: int = Field(..., ge=1, le=365, description="연장 기간 (일)")
    justification: str = Field(..., min_length=10, max_length=500, description="연장 사유")


class PermissionStatsResponse(BaseModel):
    """권한 통계 응답 모델"""
    total_active: int
    pending_approvals: int
    expiring_soon: int
    by_permission_level: dict
    by_status: dict


class ExpiringPermission(BaseModel):
    """만료 예정 권한 모델"""
    grant_id: int
    user_email: str
    user_name: str
    property_id: str
    permission_level: PermissionLevel
    expires_at: datetime
    days_until_expiry: int


class NotificationRequest(BaseModel):
    """알림 요청 모델"""
    grant_id: int
    notification_type: str = Field(..., pattern="^(approval|rejection|expiry_warning|expired)$")
    recipient_email: str
    message: Optional[str] = None 