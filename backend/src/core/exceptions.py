"""
Custom exceptions for GA4 Admin Automation System
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationError(AppException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(AppException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundError(AppException):
    """Not found error exception"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND"
        )


class ConflictError(AppException):
    """Conflict error exception"""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR"
        )


class RateLimitError(AppException):
    """Rate limit error exception"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_ERROR"
        )


class GoogleAPIError(AppException):
    """Google API error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="GOOGLE_API_ERROR",
            details=details
        )


class EmailError(AppException):
    """Email sending error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="EMAIL_ERROR",
            details=details
        )


class SecurityError(AppException):
    """Security error exception for security-related issues"""
    
    def __init__(self, message: str = "Security violation detected", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=429,  # Too Many Requests for brute force attempts
            error_code="SECURITY_ERROR",
            details=details
        )


class SessionError(AppException):
    """Session management error exception"""
    
    def __init__(self, message: str = "Session error occurred", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="SESSION_ERROR",
            details=details
        )


class RegistrationError(AppException):
    """User registration error exception"""
    
    def __init__(self, message: str = "Registration failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="REGISTRATION_ERROR",
            details=details
        )


class VerificationError(AppException):
    """Email verification error exception"""
    
    def __init__(self, message: str = "Verification failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VERIFICATION_ERROR",
            details=details
        )


class ApprovalError(AppException):
    """User approval error exception"""
    
    def __init__(self, message: str = "Approval process failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="APPROVAL_ERROR",
            details=details
        )


class PropertyAccessError(AppException):
    """Property access error exception"""
    
    def __init__(self, message: str = "Property access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PROPERTY_ACCESS_ERROR",
            details=details
        )


class AuditError(AppException):
    """Audit logging error exception"""
    
    def __init__(self, message: str = "Audit logging failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="AUDIT_ERROR",
            details=details
        )


class ConfigurationError(AppException):
    """Configuration error exception"""
    
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


# Aliases for backward compatibility
PermissionDeniedError = AuthorizationError


def create_http_exception(exception: AppException):
    """Convert AppException to HTTPException for FastAPI"""
    from fastapi import HTTPException
    
    return HTTPException(
        status_code=exception.status_code,
        detail={
            "message": exception.message,
            "error_code": exception.error_code,
            "details": exception.details
        }
    )