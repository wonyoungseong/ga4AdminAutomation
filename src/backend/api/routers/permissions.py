"""
권한 관리 API 라우터
==================

권한 신청, 승인, 만료 관리 등의 API 엔드포인트들
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi.responses import JSONResponse
import logging

from src.backend.models.permission_models import (
    PermissionRequestCreate, PermissionRequestResponse,
    PermissionApprovalRequest, PermissionExtensionRequest,
    PermissionStatsResponse, ExpiringPermission
)
from src.backend.services.permission_service import get_permission_service, PermissionService
from src.backend.core.dependencies import get_current_user, require_admin

# 라우터 인스턴스 생성
router = APIRouter(prefix="/permissions", tags=["권한 관리"])


@router.post("/request", response_model=PermissionRequestResponse)
async def submit_permission_request(
    request: PermissionRequestCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    GA4 속성에 대한 권한을 신청합니다.
    
    - **property_id**: GA4 속성 ID (예: 123456789)
    - **permission_level**: 권한 수준 (viewer, analyst, editor, administrator)
    - **requested_duration_days**: 신청 기간 (일)
    - **justification**: 신청 사유
    
    Viewer/Analyst 권한은 자동 승인되며, Editor/Administrator 권한은 관리자 승인이 필요합니다.
    """
    try:
        # 사용자가 requester 역할인지 확인
        if current_user.get("role") != "requester":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="권한 신청은 신청자 역할의 사용자만 가능합니다"
            )
        
        # 권한 신청 처리
        return await permission_service.submit_permission_request(
            user_id=current_user["user_id"],
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 신청 처리 중 오류가 발생했습니다"
        )


@router.get("/my-requests", response_model=List[PermissionRequestResponse])
async def get_my_permission_requests(
    status_filter: Optional[str] = Query(None, description="상태별 필터링 (pending, active, rejected, expired)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    현재 사용자의 권한 신청 이력을 조회합니다.
    
    - **status_filter**: 특정 상태의 신청만 필터링 (선택사항)
    """
    try:
        # TODO: 개별 사용자의 신청 이력 조회 로직 구현
        # 현재는 임시로 빈 리스트 반환
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 신청 이력 조회 중 오류가 발생했습니다"
        )


@router.get("/pending", response_model=List[PermissionRequestResponse])
async def get_pending_requests(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환할 레코드 수"),
    admin_user: Dict[str, Any] = Depends(require_admin),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    승인 대기 중인 권한 신청 목록을 조회합니다. (관리자 전용)
    
    - **skip**: 페이지네이션용 건너뛸 레코드 수
    - **limit**: 한 번에 반환할 최대 레코드 수
    """
    try:
        return await permission_service.get_pending_requests(skip=skip, limit=limit)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="승인 대기 목록 조회 중 오류가 발생했습니다"
        )


@router.post("/approve")
async def approve_permission_request(
    approval: PermissionApprovalRequest,
    admin_user: Dict[str, Any] = Depends(require_admin),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    권한 신청을 승인하거나 거부합니다. (관리자 전용)
    
    - **grant_id**: 처리할 권한 신청 ID
    - **action**: 처리 액션 ('approve' 또는 'reject')
    - **admin_notes**: 관리자 메모 (선택사항)
    - **custom_duration_days**: 사용자 정의 기간 (선택사항, 승인 시)
    """
    try:
        return await permission_service.approve_permission_request(
            approval=approval,
            admin_user_id=admin_user["user_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 승인 처리 중 오류가 발생했습니다"
        )


@router.get("/expiring", response_model=List[ExpiringPermission])
async def get_expiring_permissions(
    days: int = Query(30, ge=1, le=365, description="몇 일 이내 만료"),
    admin_user: Dict[str, Any] = Depends(require_admin),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    지정된 일수 내에 만료될 권한 목록을 조회합니다. (관리자 전용)
    
    - **days**: 몇 일 이내에 만료될 권한을 조회할지 지정 (기본값: 30일)
    """
    try:
        return await permission_service.get_expiring_permissions(days=days)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="만료 예정 권한 조회 중 오류가 발생했습니다"
        )


@router.get("/stats", response_model=PermissionStatsResponse)
async def get_permission_stats(
    admin_user: Dict[str, Any] = Depends(require_admin),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    권한 관련 통계 정보를 조회합니다. (관리자 전용)
    
    전체 활성 권한 수, 승인 대기 건수, 만료 예정 권한 수 등의 통계를 제공합니다.
    """
    try:
        stats = await permission_service.get_permission_stats()
        return PermissionStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 통계 조회 중 오류가 발생했습니다"
        )


@router.post("/extend")
async def request_permission_extension(
    extension: PermissionExtensionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    활성 권한의 연장을 요청합니다.
    
    - **grant_id**: 연장할 권한 ID
    - **extension_days**: 연장 기간 (일)
    - **justification**: 연장 사유
    
    Viewer/Analyst 권한은 자동 연장되며, Editor/Administrator 권한은 관리자 승인이 필요합니다.
    """
    try:
        # TODO: 권한 연장 요청 로직 구현
        return {
            "message": "권한 연장 요청이 제출되었습니다",
            "grant_id": extension.grant_id,
            "extension_days": extension.extension_days,
            "status": "pending_extension"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 연장 요청 처리 중 오류가 발생했습니다"
        )


@router.get("/active", response_model=List[PermissionRequestResponse])
async def get_active_permissions(
    user_id: Optional[int] = Query(None, description="특정 사용자 필터링"),
    property_id: Optional[str] = Query(None, description="특정 속성 필터링"),
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환할 레코드 수"),
    admin_user: Dict[str, Any] = Depends(require_admin),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    현재 활성 상태인 권한 목록을 조회합니다. (관리자 전용)
    
    - **user_id**: 특정 사용자의 권한만 필터링 (선택사항)
    - **property_id**: 특정 GA4 속성의 권한만 필터링 (선택사항)
    - **skip**: 페이지네이션용 건너뛸 레코드 수
    - **limit**: 한 번에 반환할 최대 레코드 수
    """
    try:
        return await permission_service.get_active_permissions(
            user_id=user_id,
            property_id=property_id,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="활성 권한 목록 조회 중 오류가 발생했습니다"
        )


@router.delete("/{grant_id}/revoke")
async def revoke_permission(
    grant_id: int,
    reason: Optional[str] = Query(None, description="철회 사유"),
    admin_user: Dict[str, Any] = Depends(require_admin),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    활성 권한을 강제로 철회합니다. (관리자 전용)
    
    - **grant_id**: 철회할 권한 ID
    - **reason**: 철회 사유 (선택사항)
    
    GA4에서도 해당 사용자의 권한이 즉시 제거됩니다.
    """
    try:
        return await permission_service.revoke_permission(
            grant_id=grant_id,
            reason=reason,
            admin_user_id=admin_user["user_id"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 철회 처리 중 오류가 발생했습니다"
        ) 