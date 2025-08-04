"""
Authentication service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.config import settings
from ..core.database import get_db
from ..core.exceptions import AuthenticationError
from ..models.db_models import User
from ..models.schemas import UserLogin, Token

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token security
security = HTTPBearer()


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return tokens"""
        user = await self.get_user_by_email(login_data.email)
        
        if not user or not self.verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        
        if user.status != "active":
            raise AuthenticationError("Account is not active")
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.db.commit()
        
        # Create tokens
        token_data = {"sub": user.email, "user_id": user.id, "role": user.role.value}
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": user.email, "user_id": user.id})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not email or not user_id:
            raise AuthenticationError("Invalid token payload")
        
        user = await self.get_user_by_email(email)
        if not user or user.id != user_id:
            raise AuthenticationError("User not found")
        
        if user.status != "active":
            raise AuthenticationError("Account is not active")
        
        # Create new tokens
        token_data = {"sub": user.email, "user_id": user.id, "role": user.role.value}
        access_token = self.create_access_token(token_data)
        new_refresh_token = self.create_refresh_token({"sub": user.email, "user_id": user.id})
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def get_current_user(
        token: str = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get current authenticated user from token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = AuthService.verify_token(token.credentials)
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            role: str = payload.get("role")
            
            if email is None or user_id is None:
                raise credentials_exception
                
        except JWTError:
            raise credentials_exception
        
        # Verify user still exists and is active
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None or user.status != "active":
            raise credentials_exception
        
        return {
            "user_id": user_id,
            "email": email,
            "role": role or user.role.value,  # Use token role or fallback to DB role
            "user": user
        }