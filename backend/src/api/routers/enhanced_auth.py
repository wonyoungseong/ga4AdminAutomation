"""
Enhanced Authentication API routes with Session Management and Security Features
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Dict, Any
from datetime import datetime

from ...core.database import get_db
from ...core.exceptions import AuthenticationError, ValidationError, SecurityError
from ...models.schemas import (
    UserLogin, Token, UserResponse, UserRegistrationRequest,
    EmailVerificationRequest
)
from ...services.enhanced_auth_service import EnhancedAuthService
from ...services.enhanced_user_service import EnhancedUserService

router = APIRouter()
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegistrationRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user with enhanced workflow"""
    try:
        user_service = EnhancedUserService(db)
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        user = await user_service.register_user(
            user_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return user
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Verify user email with token"""
    try:
        user_service = EnhancedUserService(db)
        success = await user_service.verify_email(verification_data.token)
        
        if success:
            return {
                "message": "Email verified successfully. Your account is now pending approval.",
                "status": "verified"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@router.post("/login")
async def login(
    login_data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Authenticate user and return access token with enhanced security"""
    try:
        auth_service = EnhancedAuthService(db)
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        token, user = await auth_service.authenticate_user(
            login_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "user": user
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except SecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
            headers={"Retry-After": "900"}  # 15 minutes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Refresh access token using refresh token"""
    try:
        auth_service = EnhancedAuthService(db)
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        token = await auth_service.refresh_access_token(
            refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[dict, Depends(EnhancedAuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Logout user and terminate session"""
    try:
        auth_service = EnhancedAuthService(db)
        session_id = current_user.get("session_id")
        user_id = current_user.get("user_id")
        ip_address = get_client_ip(request)
        
        if session_id:
            success = await auth_service.logout_user(
                session_token=session_id,
                user_id=user_id,
                ip_address=ip_address,
                reason="user_logout"
            )
            
            if success:
                return {"message": "Successfully logged out"}
            else:
                return {"message": "Session already terminated"}
        else:
            return {"message": "No active session found"}
            
    except Exception as e:
        # Don't fail logout even if logging fails
        return {"message": "Logged out (with warnings)", "warning": str(e)}


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: Annotated[dict, Depends(EnhancedAuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Logout user from all sessions"""
    try:
        user_service = EnhancedUserService(db)
        user_id = current_user.get("user_id")
        
        # Get all active sessions for the user
        from sqlalchemy import select, and_
        from ...models.db_models import UserSession
        
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
        )
        sessions = result.scalars().all()
        
        # Terminate all sessions
        terminated_count = 0
        for session in sessions:
            if session.terminate_session("user_logout_all"):
                terminated_count += 1
        
        await db.commit()
        
        return {
            "message": f"Successfully logged out from {terminated_count} sessions",
            "terminated_sessions": terminated_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout all failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[dict, Depends(EnhancedAuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get current authenticated user profile"""
    try:
        user_service = EnhancedUserService(db)
        user = await user_service.get_user_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )


@router.get("/sessions")
async def get_user_sessions(
    current_user: Annotated[dict, Depends(EnhancedAuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get user's active sessions"""
    try:
        from sqlalchemy import select, and_
        from ...models.db_models import UserSession
        
        user_id = current_user.get("user_id")
        
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            ).order_by(UserSession.last_activity_at.desc())
        )
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
            session_info = {
                "id": session.id,
                "ip_address": str(session.ip_address),
                "user_agent": session.user_agent,
                "created_at": session.created_at,
                "last_activity_at": session.last_activity_at,
                "expires_at": session.expires_at,
                "is_current": session.session_token == current_user.get("session_id"),
                "device_fingerprint": session.device_fingerprint
            }
            session_list.append(session_info)
        
        return {
            "sessions": session_list,
            "total_sessions": len(session_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: int,
    current_user: Annotated[dict, Depends(EnhancedAuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Terminate a specific session"""
    try:
        from sqlalchemy import select, and_
        from ...models.db_models import UserSession
        
        user_id = current_user.get("user_id")
        
        # Get the session
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.id == session_id,
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already terminated"
            )
        
        # Terminate the session
        success = session.terminate_session("user_manual_termination")
        
        if success:
            # Log the termination
            user_service = EnhancedUserService(db)
            await user_service.log_user_activity(
                user_id=user_id,
                activity_type="auth",
                action="session_terminated",
                resource_type="session",
                resource_id=str(session_id),
                details={"terminated_session_id": session_id}
            )
            
            await db.commit()
            
            return {"message": "Session terminated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to terminate session"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session termination failed: {str(e)}"
        )


@router.post("/check-password-strength")
async def check_password_strength(
    password_data: Dict[str, str],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Check password strength and provide recommendations"""
    try:
        password = password_data.get("password")
        if not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password is required"
            )
        
        auth_service = EnhancedAuthService(db)
        strength_info = await auth_service.check_password_strength(password)
        
        return strength_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password strength check failed: {str(e)}"
        )


@router.get("/security-info")
async def get_security_info(
    request: Request,
    current_user: Annotated[dict, Depends(EnhancedAuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get current security information for the user"""
    try:
        from sqlalchemy import select, and_, desc, func
        from ...models.db_models import UserActivityLog, UserSession
        
        user_id = current_user.get("user_id")
        ip_address = get_client_ip(request)
        
        # Get recent login activities
        recent_logins = await db.execute(
            select(UserActivityLog).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.activity_type == "auth",
                    UserActivityLog.action.like("login_%")
                )
            ).order_by(desc(UserActivityLog.created_at)).limit(5)
        )
        login_activities = recent_logins.scalars().all()
        
        # Get session statistics
        session_stats = await db.execute(
            select(
                func.count(UserSession.id).label('total_sessions'),
                func.count(
                    func.case(
                        (UserSession.is_active == True, 1)
                    )
                ).label('active_sessions')
            ).where(UserSession.user_id == user_id)
        )
        stats = session_stats.first()
        
        # Check for suspicious activities
        suspicious_activities = await db.execute(
            select(UserActivityLog).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.success == False,
                    UserActivityLog.created_at >= func.now() - func.interval('7 days')
                )
            ).order_by(desc(UserActivityLog.created_at)).limit(10)
        )
        suspicious = suspicious_activities.scalars().all()\n        \n        return {\n            \"current_ip\": ip_address,\n            \"session_statistics\": {\n                \"total_sessions\": stats.total_sessions or 0,\n                \"active_sessions\": stats.active_sessions or 0\n            },\n            \"recent_login_activities\": [\n                {\n                    \"action\": activity.action,\n                    \"ip_address\": str(activity.ip_address) if activity.ip_address else None,\n                    \"success\": activity.success,\n                    \"created_at\": activity.created_at,\n                    \"user_agent\": activity.user_agent\n                }\n                for activity in login_activities\n            ],\n            \"suspicious_activities\": [\n                {\n                    \"action\": activity.action,\n                    \"ip_address\": str(activity.ip_address) if activity.ip_address else None,\n                    \"created_at\": activity.created_at,\n                    \"error_message\": activity.error_message\n                }\n                for activity in suspicious\n            ],\n            \"security_recommendations\": await _get_security_recommendations(user_id, db)\n        }\n        \n    except Exception as e:\n        raise HTTPException(\n            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n            detail=f\"Failed to retrieve security info: {str(e)}\"\n        )\n\n\nasync def _get_security_recommendations(user_id: int, db: AsyncSession) -> list:\n    \"\"\"Generate security recommendations for the user\"\"\"\n    recommendations = []\n    \n    try:\n        from sqlalchemy import select, and_, func\n        from ...models.db_models import UserSession, UserActivityLog, User\n        \n        # Check for multiple active sessions\n        active_sessions = await db.execute(\n            select(func.count(UserSession.id)).where(\n                and_(\n                    UserSession.user_id == user_id,\n                    UserSession.is_active == True\n                )\n            )\n        )\n        session_count = active_sessions.scalar()\n        \n        if session_count > 3:\n            recommendations.append({\n                \"type\": \"warning\",\n                \"message\": f\"You have {session_count} active sessions. Consider terminating unused sessions.\",\n                \"action\": \"review_sessions\"\n            })\n        \n        # Check for recent failed login attempts\n        failed_logins = await db.execute(\n            select(func.count(UserActivityLog.id)).where(\n                and_(\n                    UserActivityLog.user_id == user_id,\n                    UserActivityLog.activity_type == \"auth\",\n                    UserActivityLog.action.like(\"login_failed_%\"),\n                    UserActivityLog.created_at >= func.now() - func.interval('24 hours')\n                )\n            )\n        )\n        failed_count = failed_logins.scalar()\n        \n        if failed_count > 3:\n            recommendations.append({\n                \"type\": \"alert\",\n                \"message\": f\"{failed_count} failed login attempts in the last 24 hours. Consider changing your password.\",\n                \"action\": \"change_password\"\n            })\n        \n        # Check password age (would need to track password changes)\n        # For now, just a general recommendation\n        recommendations.append({\n            \"type\": \"info\",\n            \"message\": \"Consider enabling two-factor authentication for enhanced security.\",\n            \"action\": \"enable_2fa\"\n        })\n        \n        return recommendations\n        \n    except Exception:\n        return [{\n            \"type\": \"info\",\n            \"message\": \"Regular security review is recommended.\",\n            \"action\": \"general_review\"\n        }]