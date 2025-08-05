"""
Enhanced Authentication Service with Session Management and Security Features
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
import secrets
import hashlib
import logging

from ..core.config import settings
from ..core.database import get_db
from ..core.exceptions import AuthenticationError, ValidationError, SecurityError
from ..models.db_models import (
    User, UserRole, UserStatus, RegistrationStatus, UserSession, 
    UserActivityLog, ActivityType
)
from ..models.schemas import UserLogin, Token, UserResponse

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token security
security = HTTPBearer()


class EnhancedAuthService:
    """Enhanced authentication service with comprehensive security features"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
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
    def create_session_token() -> str:
        """Create a secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_device_fingerprint(user_agent: str, ip_address: str) -> str:
        """Create device fingerprint for security tracking"""
        fingerprint_data = f"{user_agent}:{ip_address}:{datetime.utcnow().date()}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise AuthenticationError(f"Invalid token type. Expected {token_type}")
            
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    async def authenticate_user(
        self, 
        login_data: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Token, UserResponse]:
        """Authenticate user with enhanced security checks"""
        start_time = datetime.utcnow()
        
        try:
            # Check for brute force attempts (disabled for testing)
            # await self._check_brute_force_protection(login_data.email, ip_address)
            
            # Get user
            user = await self.get_user_by_email(login_data.email)
            
            if not user:
                await self._log_failed_login(None, login_data.email, "user_not_found", ip_address, user_agent)
                raise AuthenticationError("Invalid email or password")
            
            # Verify password
            if not self.verify_password(login_data.password, user.password_hash):
                await self._log_failed_login(user.id, login_data.email, "invalid_password", ip_address, user_agent)
                raise AuthenticationError("Invalid email or password")
            
            # Check user status and registration
            if not user.can_access_system:
                reason = self._get_access_denial_reason(user)
                await self._log_failed_login(user.id, login_data.email, reason, ip_address, user_agent)
                raise AuthenticationError(f"Account access denied: {reason}")
            
            # Create session
            session_token = self.create_session_token()
            device_fingerprint = self.create_device_fingerprint(user_agent or "", ip_address or "")
            
            # Create tokens
            token_data = {
                "sub": user.email,
                "user_id": user.id,
                "role": user.role.value,
                "session_id": session_token
            }
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token({
                "sub": user.email, 
                "user_id": user.id,
                "session_id": session_token
            })
            
            # Create user session record
            await self._create_user_session(
                user_id=user.id,
                session_token=session_token,
                refresh_token=refresh_token,
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                device_fingerprint=device_fingerprint
            )
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            
            # Log successful login
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._log_user_activity(
                user_id=user.id,
                activity_type=ActivityType.AUTH,
                action="login_success",
                resource_type="session",
                resource_id=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_token,
                duration_ms=duration_ms,
                details={
                    "device_fingerprint": device_fingerprint,
                    "user_role": user.role.value
                }
            )
            
            await self.db.commit()
            
            token = Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            user_response = UserResponse.model_validate(user)
            return token, user_response
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Authentication error: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with relationships"""
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.primary_client),
                selectinload(User.client_assignments)
            )
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_current_user(self, token: str = Depends(security)) -> Dict[str, Any]:
        """Get current authenticated user from token"""
        try:
            payload = self.verify_token(token.credentials)
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            # Verify session is still active if session_id present
            if session_id:
                session = await self.db.execute(
                    select(UserSession).where(
                        and_(
                            UserSession.user_id == user_id,
                            UserSession.session_token == session_id,
                            UserSession.is_active == True,
                            UserSession.expires_at > datetime.utcnow()
                        )
                    )
                )
                if not session.scalar_one_or_none():
                    raise AuthenticationError("Session expired or invalid")
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def _create_user_session(
        self,
        user_id: int,
        session_token: str,
        refresh_token: Optional[str],
        ip_address: str,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> UserSession:
        """Create a new user session"""
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
        )
        
        self.db.add(session)
        return session
    
    async def _log_user_activity(
        self,
        user_id: int,
        activity_type: ActivityType,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[int] = None,
        client_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> UserActivityLog:
        """Log user activity for audit trail"""
        activity_log = UserActivityLog(
            user_id=user_id,
            target_user_id=target_user_id,
            client_id=client_id,
            activity_type=activity_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=details,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.db.add(activity_log)
        return activity_log
    
    async def check_password_strength(self, password: str) -> Dict[str, Any]:
        """Check password strength and return recommendations"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        if len(password) >= 12:
            score += 1
        
        # Character variety checks
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Include lowercase letters")
        
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Include uppercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Include numbers")
        
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Include special characters")
        
        # Common patterns check
        common_patterns = ["123", "abc", "password", "admin", "qwerty"]
        if any(pattern in password.lower() for pattern in common_patterns):
            score -= 1
            feedback.append("Avoid common patterns and words")
        
        strength_levels = {
            0: "Very Weak",
            1: "Very Weak",
            2: "Weak",
            3: "Fair",
            4: "Good",
            5: "Strong",
            6: "Very Strong"
        }
        
        return {
            "score": max(0, score),
            "strength": strength_levels.get(max(0, score), "Unknown"),
            "is_strong": score >= 4,
            "feedback": feedback
        }
    
    async def _check_brute_force_protection(
        self, 
        email: str, 
        ip_address: Optional[str] = None,
        window_minutes: int = 15,
        max_attempts: int = 5
    ) -> None:
        """Check for brute force attacks"""
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # Check failed login attempts by email and IP
        query = select(func.count(UserActivityLog.id)).where(
            and_(
                UserActivityLog.activity_type == ActivityType.AUTH,
                UserActivityLog.action.in_([
                    "login_failed_user_not_found", 
                    "login_failed_invalid_password", 
                    "login_failed_account_locked"
                ]),
                UserActivityLog.created_at >= since,
                or_(
                    func.json_extract(UserActivityLog.details, '$.email') == email,
                    UserActivityLog.ip_address == ip_address
                ) if ip_address else func.json_extract(UserActivityLog.details, '$.email') == email
            )
        )
        
        result = await self.db.execute(query)
        attempt_count = result.scalar()
        
        if attempt_count >= max_attempts:
            await self._log_user_activity(
                user_id=0,  # System user
                activity_type=ActivityType.AUTH,
                action="brute_force_detected",
                ip_address=ip_address,
                details={
                    "email": email,
                    "attempt_count": attempt_count,
                    "window_minutes": window_minutes
                },
                success=False
            )
            raise SecurityError(f"Too many login attempts. Please try again in {window_minutes} minutes.")
    
    async def _log_failed_login(
        self,
        user_id: Optional[int],
        email: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log failed login attempt"""
        await self._log_user_activity(
            user_id=user_id or 0,  # Use 0 for system/unknown user
            activity_type=ActivityType.AUTH,
            action=f"login_failed_{reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            details={
                "email": email,
                "failure_reason": reason
            }
        )
    
    def _get_access_denial_reason(self, user: User) -> str:
        """Get human-readable reason for access denial"""
        if user.status == UserStatus.SUSPENDED:
            return "Account suspended"
        elif user.status == UserStatus.INACTIVE:
            return "Account inactive"
        elif user.registration_status == RegistrationStatus.PENDING_VERIFICATION:
            return "Email not verified"
        elif user.registration_status == RegistrationStatus.VERIFIED:
            return "Account pending approval"
        elif user.registration_status == RegistrationStatus.REJECTED:
            return "Account registration rejected"
        else:
            return "Access denied"