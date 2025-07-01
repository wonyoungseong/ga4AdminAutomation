"""
인증 서비스
==========

JWT 토큰 기반 사용자 인증 및 권한 관리 서비스
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from passlib.hash import bcrypt
from jose import JWTError, jwt
import logging

from src.backend.core.config import get_settings
from src.backend.core.database import get_db, DatabaseService

logger = logging.getLogger(__name__)


class AuthService:
    """JWT 기반 인증 서비스 클래스"""
    
    def __init__(self):
        """AuthService 초기화"""
        self.settings = get_settings()
        self.db = get_db()
        logger.info("✅ AuthService 초기화 완료")
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm="HS256"
        )
        
        return encoded_jwt
    
    def _verify_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(
                token, 
                self.settings.secret_key, 
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증"""
        try:
            # 개발 환경용 하드코딩된 인증 (실제로는 데이터베이스에서 조회)
            if email == "admin@ga4automation.com" and password == "admin123":
                return {
                    "user_id": 1,
                    "email": email,
                    "user_name": "시스템 관리자",
                    "company": "GA 서비스 파트너",
                    "role": "super_admin",
                    "is_representative": True
                }
            
            # TODO: 실제 데이터베이스에서 사용자 조회 및 비밀번호 검증
            # 현재는 Supabase에 비밀번호 필드가 없으므로 추후 구현
            
            return None
            
        except Exception as e:
            logger.error(f"사용자 인증 실패: {e}")
            return None
    
    async def create_user_token(self, user: Dict[str, Any]) -> str:
        """사용자용 JWT 토큰 생성"""
        token_data = {
            "sub": str(user["user_id"]),
            "email": user["email"],
            "role": user["role"],
            "user_name": user["user_name"],
            "is_representative": user.get("is_representative", False)
        }
        
        access_token = self._create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=24)
        )
        
        return access_token
    
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """토큰에서 현재 사용자 정보 추출"""
        try:
            payload = self._verify_token(token)
            user_id = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="토큰에서 사용자 정보를 찾을 수 없습니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 토큰에서 사용자 정보 반환
            return {
                "user_id": int(user_id),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "user_name": payload.get("user_name"),
                "is_representative": payload.get("is_representative", False)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"현재 사용자 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자 인증에 실패했습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def check_permission(self, user: Dict[str, Any], required_role: str = None) -> bool:
        """사용자 권한 확인"""
        if not user:
            return False
        
        user_role = user.get("role")
        
        # Super Admin은 모든 권한 보유
        if user_role == "super_admin":
            return True
        
        # 특정 역할이 요구되는 경우
        if required_role:
            return user_role == required_role
        
        # 기본적으로 로그인한 사용자는 기본 권한 보유
        return True
    
    def check_admin_permission(self, user: Dict[str, Any]) -> bool:
        """관리자 권한 확인"""
        return user.get("role") == "super_admin"
    
    def check_representative_permission(self, user: Dict[str, Any]) -> bool:
        """대표자 권한 확인 (Super Admin + 대표자)"""
        return (
            user.get("role") == "super_admin" and 
            user.get("is_representative", False)
        )


# 전역 인증 서비스 인스턴스
_auth_service = None

def get_auth_service() -> AuthService:
    """인증 서비스 싱글톤 인스턴스 반환"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service 