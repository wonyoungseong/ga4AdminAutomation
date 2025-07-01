"""
사용자 관리 API 라우터
신청자 등록, 사용자 정보 조회 등을 담당합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import JSONResponse
import logging

from src.backend.core.database import get_db, DatabaseService

# 라우터 인스턴스 생성
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


# 기본 사용자 정보 스키마
class UserBase(BaseModel):
    email: str
    user_name: str
    company: str


class UserCreate(UserBase):
    """사용자 생성 요청 스키마"""
    pass


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    user_id: int
    role: str
    is_representative: bool
    role_expires_at: Optional[str] = None
    created_at: str


class UserListResponse(BaseModel):
    """사용자 목록 응답 스키마"""
    users: List[UserResponse]
    total_count: int


# 신청자 등록 엔드포인트
@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: DatabaseService = Depends(get_db)):
    """
    새로운 신청자를 등록합니다.
    
    - **email**: 사용자 이메일 (필수)
    - **user_name**: 사용자 이름 (필수)  
    - **company**: 회사명 (필수)
    
    기본적으로 'requester' 역할로 등록됩니다.
    """
    try:
        # 새 사용자 데이터 준비
        new_user_data = {
            "email": user_data.email,
            "user_name": user_data.user_name,
            "company": user_data.company,
            "role": "requester",
            "is_representative": False
        }
        
        # 데이터베이스에 사용자 생성
        created_user = await db.create_user(new_user_data)
        
        return {
            "user_id": created_user["user_id"],
            "email": created_user["email"],
            "user_name": created_user["user_name"],
            "company": created_user["company"],
            "role": created_user["role"],
            "is_representative": created_user["is_representative"],
            "role_expires_at": created_user.get("role_expires_at"),
            "created_at": created_user["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 사용자 목록 조회
@router.get("/", response_model=UserListResponse)
async def get_users(
    role: Optional[str] = None,
    is_representative: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: DatabaseService = Depends(get_db)
):
    """
    사용자 목록을 조회합니다.
    
    - **role**: 역할별 필터링 (super_admin, requester)
    - **is_representative**: 대표자 여부 필터링 (true, false)
    - **skip**: 건너뛸 레코드 수 (페이지네이션)
    - **limit**: 최대 반환할 레코드 수
    """
    try:
        # 실제 데이터베이스에서 사용자 목록 조회
        result = await db.get_all_users(limit=limit, offset=skip)
        
        # 필터링 적용 (role, is_representative)
        filtered_users = result["users"]
        if role:
            filtered_users = [user for user in filtered_users if user.get("role") == role]
        if is_representative is not None:
            filtered_users = [user for user in filtered_users if user.get("is_representative") == is_representative]
        
        return {
            "users": [
                {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "user_name": user["user_name"],
                    "company": user["company"],
                    "role": user["role"],
                    "is_representative": user["is_representative"],
                    "role_expires_at": user.get("role_expires_at"),
                    "created_at": user["created_at"]
                }
                for user in filtered_users
            ],
            "total_count": len(filtered_users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 특정 사용자 조회
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: DatabaseService = Depends(get_db)):
    """
    특정 사용자의 상세 정보를 조회합니다.
    
    - **user_id**: 사용자 ID
    """
    try:
        user = await db.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "user_name": user["user_name"],
            "company": user["company"],
            "role": user["role"],
            "is_representative": user["is_representative"],
            "role_expires_at": user.get("role_expires_at"),
            "created_at": user["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 사용자 역할 업데이트
@router.patch("/{user_id}/role")
async def update_user_role(user_id: int, new_role: str):
    """
    사용자의 역할을 업데이트합니다.
    
    - **user_id**: 사용자 ID
    - **new_role**: 새로운 역할 (super_admin, requester)
    """
    # TODO: 실제 업데이트 로직 구현
    return {
        "message": f"사용자 {user_id}의 역할이 {new_role}로 업데이트되었습니다",
        "user_id": user_id,
        "new_role": new_role
    } 