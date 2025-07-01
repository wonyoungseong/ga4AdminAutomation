"""
FastAPI 의존성 함수들
==================

인증, 권한 확인 등의 의존성 함수들
"""

from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from src.backend.services.auth_service import get_auth_service, AuthService

# HTTP Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자 정보를 반환하는 의존성 함수
    
    JWT 토큰이 필요하며, 유효하지 않으면 401 에러를 발생시킵니다.
    """
    token = credentials.credentials
    return await auth_service.get_current_user(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[Dict[str, Any]]:
    """
    현재 로그인한 사용자 정보를 반환하는 선택적 의존성 함수
    
    토큰이 없어도 None을 반환하며 에러를 발생시키지 않습니다.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return await auth_service.get_current_user(token)
    except HTTPException:
        return None


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    관리자 권한이 필요한 엔드포인트용 의존성 함수
    
    Super Admin 역할이 아니면 403 에러를 발생시킵니다.
    """
    if not auth_service.check_admin_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    return current_user


async def require_representative(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    대표자 권한이 필요한 엔드포인트용 의존성 함수
    
    Super Admin이면서 대표자가 아니면 403 에러를 발생시킵니다.
    """
    if not auth_service.check_representative_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="대표자 권한이 필요합니다"
        )
    
    return current_user


def require_role(required_role: str):
    """
    특정 역할이 필요한 엔드포인트용 의존성 함수 팩토리
    
    사용 예:
    @router.get("/requester-only")
    async def requester_endpoint(user = Depends(require_role("requester"))):
        ...
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> Dict[str, Any]:
        if not auth_service.check_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role} 역할이 필요합니다"
            )
        
        return current_user
    
    return role_checker


async def get_user_permissions(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    현재 사용자의 권한 정보를 반환하는 의존성 함수
    
    UI에서 버튼/메뉴 표시 여부를 결정할 때 사용할 수 있습니다.
    """
    role = current_user.get("role", "")
    is_representative = current_user.get("is_representative", False)
    
    return {
        "is_super_admin": role == "super_admin",
        "is_requester": role == "requester", 
        "is_representative": is_representative,
        "can_manage_users": role == "super_admin",
        "can_approve_requests": role == "super_admin",
        "can_manage_ga4": role == "super_admin",
        "can_view_dashboard": role in ["super_admin", "requester"],
        "can_submit_requests": role == "requester"
    } 