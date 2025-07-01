"""
GA4 Admin API 라우터
Google Analytics 4 관리 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
from datetime import datetime
from fastapi.responses import JSONResponse
import logging

from src.backend.services.ga4_service import get_ga4_service, GA4Service

# 라우터 인스턴스 생성
router = APIRouter(prefix="/ga4", tags=["Google Analytics 4"])


# 요청/응답 모델들
class UserRegistrationRequest(BaseModel):
    """사용자 등록 요청 스키마"""
    property_id: str
    email: EmailStr
    role: str = "viewer"  # viewer, analyst, editor, admin
    

class UserRemovalRequest(BaseModel):
    """사용자 제거 요청 스키마"""
    property_id: str
    email: EmailStr
    binding_name: Optional[str] = None


class GA4UserInfo(BaseModel):
    """GA4 사용자 정보 스키마"""
    name: str
    email: str
    roles: List[str]


class GA4PropertyUsersResponse(BaseModel):
    """GA4 속성 사용자 목록 응답 스키마"""
    property_id: str
    users: List[GA4UserInfo]
    total_count: int


class GA4ActionResponse(BaseModel):
    """GA4 작업 응답 스키마"""
    success: bool
    message: str
    binding_name: Optional[str] = None
    timestamp: str


# GA4 API 엔드포인트들

@router.post("/users/register", response_model=GA4ActionResponse)
async def register_user_to_property(
    request: UserRegistrationRequest,
    ga4_service: GA4Service = Depends(get_ga4_service)
):
    """
    GA4 속성에 사용자를 등록합니다.
    
    - **property_id**: GA4 속성 ID (예: 123456789)
    - **email**: 등록할 사용자 이메일
    - **role**: 사용자 역할 (viewer, analyst, editor, admin)
    
    성공 시 바인딩명을 반환하여 나중에 사용자 제거 시 활용할 수 있습니다.
    """
    try:
        # 역할 유효성 검사
        valid_roles = ["viewer", "analyst", "editor", "admin"]
        if request.role not in valid_roles:
            raise HTTPException(
                status_code=400, 
                detail=f"지원되지 않는 역할입니다. 가능한 역할: {', '.join(valid_roles)}"
            )
        
        # GA4 API 호출
        success, message, binding_name = await ga4_service.register_user_to_property(
            property_id=request.property_id,
            email=request.email,
            role=request.role
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return GA4ActionResponse(
            success=True,
            message=message,
            binding_name=binding_name,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 등록 중 오류가 발생했습니다: {str(e)}")


@router.delete("/users/remove", response_model=GA4ActionResponse)
async def remove_user_from_property(
    request: UserRemovalRequest,
    ga4_service: GA4Service = Depends(get_ga4_service)
):
    """
    GA4 속성에서 사용자를 제거합니다.
    
    - **property_id**: GA4 속성 ID
    - **email**: 제거할 사용자 이메일
    - **binding_name**: 바인딩명 (선택사항, 없으면 자동 검색)
    
    바인딩명을 제공하면 더 빠르게 처리됩니다.
    """
    try:
        # GA4 API 호출
        success, message = await ga4_service.remove_user_from_property(
            property_id=request.property_id,
            email=request.email,
            binding_name=request.binding_name
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return GA4ActionResponse(
            success=True,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 제거 중 오류가 발생했습니다: {str(e)}")


@router.get("/properties/{property_id}/users", response_model=GA4PropertyUsersResponse)
async def list_property_users(
    property_id: str,
    ga4_service: GA4Service = Depends(get_ga4_service)
):
    """
    GA4 속성의 모든 사용자 목록을 조회합니다.
    
    - **property_id**: GA4 속성 ID
    
    해당 속성에 접근 권한이 있는 모든 사용자와 그들의 역할을 반환합니다.
    """
    try:
        # GA4 API 호출
        users_data = await ga4_service.list_property_users(property_id)
        
        # 응답 형식으로 변환
        users = [
            GA4UserInfo(
                name=user["name"],
                email=user["email"],
                roles=user["roles"]
            )
            for user in users_data
        ]
        
        return GA4PropertyUsersResponse(
            property_id=property_id,
            users=users,
            total_count=len(users)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/test/connection")
async def test_ga4_connection(ga4_service: GA4Service = Depends(get_ga4_service)):
    """
    GA4 API 연결 상태를 테스트합니다.
    
    Service Account 설정과 API 접근 권한을 확인합니다.
    """
    try:
        # 간단한 테스트용 속성 ID (실제로는 존재하지 않을 수 있음)
        test_property_id = "123456789"
        
        # 테스트 사용자 목록 조회 시도
        users = await ga4_service.list_property_users(test_property_id)
        
        return {
            "status": "connected",
            "message": "GA4 API 연결 성공",
            "test_property_id": test_property_id,
            "test_users_found": len(users),
            "client_initialized": ga4_service.client is not None,
            "test_mode": ga4_service._is_test_environment(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"GA4 API 연결 테스트 실패: {str(e)}",
            "client_initialized": ga4_service.client is not None,
            "test_mode": ga4_service._is_test_environment(),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/roles")
async def get_available_roles():
    """
    GA4에서 사용 가능한 역할 목록을 조회합니다.
    
    각 역할의 설명과 권한 수준을 포함합니다.
    """
    roles_info = {
        "viewer": {
            "name": "viewer",
            "display_name": "뷰어",
            "description": "데이터 조회만 가능합니다.",
            "permissions": ["읽기 전용 접근"]
        },
        "analyst": {
            "name": "analyst", 
            "display_name": "분석가",
            "description": "데이터 조회 및 기본 분석 기능을 사용할 수 있습니다.",
            "permissions": ["읽기 전용 접근", "표준 보고서", "맞춤 보고서"]
        },
        "editor": {
            "name": "editor",
            "display_name": "편집자", 
            "description": "데이터 조회 및 구성 변경이 가능합니다.",
            "permissions": ["읽기/쓰기 접근", "구성 변경", "이벤트 설정"]
        },
        "admin": {
            "name": "admin",
            "display_name": "관리자",
            "description": "모든 권한을 가지며 사용자 관리가 가능합니다.",
            "permissions": ["모든 권한", "사용자 관리", "계정 설정"]
        }
    }
    
    return {
        "available_roles": list(roles_info.keys()),
        "roles_details": roles_info,
        "default_role": "viewer",
        "recommended_duration": {
            "viewer": "60일",
            "analyst": "60일", 
            "editor": "7일",
            "admin": "90일"
        }
    } 