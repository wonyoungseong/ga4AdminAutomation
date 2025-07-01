"""
인증 관련 API 라우터
JWT 토큰 기반 인증을 처리합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.backend.services.auth_service import get_auth_service, AuthService
from src.backend.core.dependencies import get_current_user, get_user_permissions

# 라우터 인스턴스 생성
router = APIRouter(prefix="/auth", tags=["인증"])


# 인증 관련 스키마
class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24시간 (초)
    user_info: Dict[str, Any]


class UserProfile(BaseModel):
    """사용자 프로필 스키마"""
    user_id: int
    email: str
    user_name: str
    company: str
    role: str
    is_representative: bool
    permissions: Dict[str, bool]


class TokenValidation(BaseModel):
    """토큰 검증 응답 스키마"""
    valid: bool
    user_info: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, bool]] = None


# 로그인 엔드포인트
@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    사용자 로그인을 처리하고 JWT 토큰을 발급합니다.
    
    - **email**: 사용자 이메일
    - **password**: 비밀번호
    
    성공 시 JWT 액세스 토큰과 사용자 정보를 반환합니다.
    """
    try:
        # 사용자 인증
        user = await auth_service.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # JWT 토큰 생성
        access_token = await auth_service.create_user_token(user)
        
        return LoginResponse(
            access_token=access_token,
            user_info=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )


# 토큰 검증 엔드포인트
@router.get("/verify", response_model=TokenValidation)
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user),
    permissions: Dict[str, bool] = Depends(get_user_permissions)
):
    """
    현재 JWT 토큰의 유효성을 검증하고 사용자 정보를 반환합니다.
    
    헤더에 Bearer 토큰을 포함하여 요청하세요.
    유효한 토큰인 경우 사용자 정보와 권한 정보를 반환합니다.
    """
    return TokenValidation(
        valid=True,
        user_info=current_user,
        permissions=permissions
    )


# 사용자 프로필 조회 엔드포인트
@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    permissions: Dict[str, bool] = Depends(get_user_permissions)
):
    """
    현재 로그인한 사용자의 프로필 정보를 조회합니다.
    
    JWT 토큰으로 인증된 요청이 필요합니다.
    사용자의 기본 정보와 권한 정보를 포함하여 반환합니다.
    """
    return UserProfile(
        user_id=current_user["user_id"],
        email=current_user["email"],
        user_name=current_user["user_name"],
        company=current_user.get("company", ""),
        role=current_user["role"],
        is_representative=current_user.get("is_representative", False),
        permissions=permissions
    )


# 로그아웃 엔드포인트
@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    사용자 로그아웃을 처리합니다.
    
    현재 구현에서는 클라이언트 측에서 토큰을 삭제하는 것으로 충분합니다.
    향후 토큰 블랙리스트 기능을 추가할 수 있습니다.
    """
    return {
        "message": "성공적으로 로그아웃되었습니다",
        "user_email": current_user["email"],
        "logged_out_at": datetime.now().isoformat()
    }


# 권한 정보 조회 엔드포인트
@router.get("/permissions")
async def get_permissions(permissions: Dict[str, bool] = Depends(get_user_permissions)):
    """
    현재 사용자의 권한 정보를 조회합니다.
    
    UI에서 버튼/메뉴 표시 여부를 결정할 때 사용할 수 있습니다.
    """
    return {
        "permissions": permissions,
        "checked_at": datetime.now().isoformat()
    } 