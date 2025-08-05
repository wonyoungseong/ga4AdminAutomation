"""
Database models for GA4 Admin Automation System
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    REQUESTER = "Requester"
    VIEWER = "Viewer"


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class PermissionLevel(str, enum.Enum):
    """GA4 permission level enumeration"""
    VIEWER = "viewer"
    ANALYST = "analyst"
    MARKETER = "marketer"
    EDITOR = "editor"
    ADMINISTRATOR = "administrator"


class PermissionStatus(str, enum.Enum):
    """Permission grant status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PermissionRequestStatus(str, enum.Enum):
    """Permission request status enumeration"""
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class NotificationChannel(str, enum.Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    SLACK = "slack"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class ReportType(str, enum.Enum):
    """Report type enumeration"""
    USER_ACTIVITY = "user_activity"
    PERMISSION_SUMMARY = "permission_summary"
    AUDIT_LOG = "audit_log"
    SYSTEM_METRICS = "system_metrics"
    COMPLIANCE_REPORT = "compliance_report"


class ClientAssignmentStatus(str, enum.Enum):
    """Client assignment status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class RegistrationStatus(str, enum.Enum):
    """User registration status enumeration"""
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class PropertyAccessStatus(str, enum.Enum):
    """Property access status enumeration"""
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ActivityType(str, enum.Enum):
    """User activity type enumeration"""
    AUTH = "auth"
    USER_MANAGEMENT = "user_management"
    PERMISSION_MANAGEMENT = "permission_management"
    CLIENT_MANAGEMENT = "client_management"
    SYSTEM_ADMIN = "system_admin"
    API_ACCESS = "api_access"


class PriorityLevel(str, enum.Enum):
    """Request priority level enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AccessLevel(str, enum.Enum):
    """Client access level enumeration"""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    FULL = "full"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.REQUESTER)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    role_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_representative: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Password reset tracking
    password_reset_count: Mapped[int] = mapped_column(Integer, default=0)
    last_password_reset: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Enhanced registration and verification fields
    registration_status: Mapped[RegistrationStatus] = mapped_column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING_VERIFICATION)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Approval workflow
    approval_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Enhanced user profile
    primary_client_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clients.id"))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Relationships
    permission_grants: Mapped[list["PermissionGrant"]] = relationship(
        "PermissionGrant", 
        back_populates="user",
        foreign_keys="PermissionGrant.user_id",
        cascade="all, delete-orphan"
    )
    user_permissions: Mapped[list["UserPermission"]] = relationship(
        "UserPermission", back_populates="user", foreign_keys="UserPermission.user_id", cascade="all, delete-orphan"
    )
    client_assignments: Mapped[list["ClientAssignment"]] = relationship(
        "ClientAssignment", back_populates="user", foreign_keys="ClientAssignment.user_id", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor", cascade="all, delete-orphan"
    )
    
    # New relationships for enhanced user management
    approved_by: Mapped[Optional["User"]] = relationship("User", remote_side=[id], foreign_keys=[approved_by_id])
    primary_client: Mapped[Optional["Client"]] = relationship("Client", foreign_keys=[primary_client_id])
    property_access_requests: Mapped[list["PropertyAccessRequest"]] = relationship(
        "PropertyAccessRequest", back_populates="user", foreign_keys="PropertyAccessRequest.user_id", cascade="all, delete-orphan"
    )
    user_activity_logs: Mapped[list["UserActivityLog"]] = relationship(
        "UserActivityLog", back_populates="user", foreign_keys="UserActivityLog.user_id", cascade="all, delete-orphan"
    )
    user_sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    
    @property
    def is_verified(self) -> bool:
        """Check if user email is verified"""
        return self.email_verified_at is not None
    
    @property
    def is_approved(self) -> bool:
        """Check if user is approved for system access"""
        return self.registration_status == RegistrationStatus.APPROVED
    
    @property
    def can_access_system(self) -> bool:
        """Check if user can access the system"""
        return (
            self.is_verified and 
            self.is_approved and 
            self.status == UserStatus.ACTIVE
        )
    
    def verify_email(self) -> bool:
        """Mark user email as verified"""
        if self.registration_status == RegistrationStatus.PENDING_VERIFICATION:
            self.email_verified_at = datetime.utcnow()
            self.registration_status = RegistrationStatus.VERIFIED
            self.verification_token = None
            self.verification_token_expires_at = None
            return True
        return False
    
    def approve_user(self, approver_id: int) -> bool:
        """Approve user for system access"""
        if self.registration_status in [RegistrationStatus.VERIFIED, RegistrationStatus.REJECTED]:
            self.registration_status = RegistrationStatus.APPROVED
            self.approved_at = datetime.utcnow()
            self.approved_by_id = approver_id
            self.rejection_reason = None
            return True
        return False
    
    def reject_user(self, reason: str) -> bool:
        """Reject user registration"""
        if self.registration_status in [RegistrationStatus.VERIFIED, RegistrationStatus.APPROVED]:
            self.registration_status = RegistrationStatus.REJECTED
            self.rejection_reason = reason
            return True
        return False


class Client(Base):
    """Client (customer company) model"""
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    service_accounts: Mapped[list["ServiceAccount"]] = relationship(
        "ServiceAccount", back_populates="client", cascade="all, delete-orphan"
    )
    ga4_properties: Mapped[list["GA4Property"]] = relationship(
        "GA4Property", back_populates="client", cascade="all, delete-orphan"
    )
    permission_grants: Mapped[list["PermissionGrant"]] = relationship(
        "PermissionGrant", back_populates="client", cascade="all, delete-orphan"
    )
    client_assignments: Mapped[list["ClientAssignment"]] = relationship(
        "ClientAssignment", back_populates="client", cascade="all, delete-orphan"
    )


class ServiceAccount(Base):
    """Google service account model"""
    __tablename__ = "service_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    secret_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Secret Manager key
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    project_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Health and usage tracking
    health_status: Mapped[str] = mapped_column(String(20), default='unknown')  # 'healthy', 'unhealthy', 'warning', 'unknown'
    health_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    key_version: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="service_accounts")
    permission_grants: Mapped[list["PermissionGrant"]] = relationship(
        "PermissionGrant", back_populates="service_account", cascade="all, delete-orphan"
    )
    service_account_properties: Mapped[list["ServiceAccountProperty"]] = relationship(
        "ServiceAccountProperty", back_populates="service_account", cascade="all, delete-orphan"
    )
    property_access_bindings: Mapped[list["PropertyAccessBinding"]] = relationship(
        "PropertyAccessBinding", back_populates="service_account", cascade="all, delete-orphan"
    )


class PermissionGrant(Base):
    """GA4 permission grant model"""
    __tablename__ = "permission_grants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    service_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    
    # GA4 specific fields
    ga_property_id: Mapped[str] = mapped_column(String(50), nullable=False)
    target_email: Mapped[str] = mapped_column(String(255), nullable=False)
    permission_level: Mapped[PermissionLevel] = mapped_column(Enum(PermissionLevel), nullable=False)
    
    # Status and lifecycle
    status: Mapped[PermissionStatus] = mapped_column(Enum(PermissionStatus), default=PermissionStatus.PENDING)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Metadata
    reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Legacy-style extension tracking
    extension_count: Mapped[int] = mapped_column(Integer, default=0)
    original_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Revocation tracking
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # GA4 synchronization fields
    binding_name: Mapped[Optional[str]] = mapped_column(String(500))  # Google's binding resource name
    synchronized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'synced', 'failed'
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="permission_grants", foreign_keys=[user_id])
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])
    revoked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[revoked_by_id])
    client: Mapped["Client"] = relationship("Client", back_populates="permission_grants")
    service_account: Mapped["ServiceAccount"] = relationship("ServiceAccount", back_populates="permission_grants")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="permission_grant", cascade="all, delete-orphan"
    )
    
    @property
    def is_active(self) -> bool:
        """Check if permission grant is currently active"""
        return (
            self.status == PermissionStatus.APPROVED and
            (self.expires_at is None or self.expires_at > datetime.utcnow())
        )
    
    @property
    def days_until_expiry(self) -> int:
        """Days until permission expires"""
        if not self.expires_at or self.expires_at <= datetime.utcnow():
            return 0
        return (self.expires_at - datetime.utcnow()).days
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if permission expires within 7 days"""
        return self.expires_at and 0 <= self.days_until_expiry <= 7
    
    def extend_permission(self, additional_days: int, extender_id: int) -> bool:
        """Extend permission - Legacy style"""
        if not self.is_active or not self.expires_at:
            return False
        
        # Set original expiry date on first extension
        if self.extension_count == 0:
            self.original_expires_at = self.expires_at
        
        self.expires_at = self.expires_at + timedelta(days=additional_days)
        self.extension_count += 1
        self.updated_at = datetime.utcnow()
        return True
    
    def revoke_permission(self, revoker_id: int, reason: str) -> bool:
        """Revoke permission - Legacy style"""
        if self.status != PermissionStatus.APPROVED:
            return False
        
        self.status = PermissionStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_by_id = revoker_id
        self.revocation_reason = reason
        self.updated_at = datetime.utcnow()
        
        # Add revocation note
        if self.notes:
            self.notes = f"{self.notes}\n\nRevoked: {reason}"
        else:
            self.notes = f"Revoked: {reason}"
        
        return True
    
    def can_extend(self) -> bool:
        """Check if permission can be extended"""
        return (
            self.is_active and
            self.extension_count < 3 and  # Max 3 extensions
            self.expires_at is not None
        )


class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Security tracking
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")


class ClientAssignment(Base):
    """Client assignment model - links users to clients with metadata"""
    __tablename__ = "client_assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    assigned_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Assignment metadata
    status: Mapped[ClientAssignmentStatus] = mapped_column(Enum(ClientAssignmentStatus), default=ClientAssignmentStatus.ACTIVE)
    assignment_type: Mapped[str] = mapped_column(String(20), default="manual")  # manual, auto, inherited
    access_level: Mapped[AccessLevel] = mapped_column(Enum(AccessLevel), default=AccessLevel.STANDARD)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Enhanced tracking
    department: Mapped[Optional[str]] = mapped_column(String(100))
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deactivated_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    deactivation_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tracking fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="client_assignments", foreign_keys=[user_id])
    client: Mapped["Client"] = relationship("Client", back_populates="client_assignments")
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_id])
    deactivated_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[deactivated_by_id])
    
    @property
    def is_active_assignment(self) -> bool:
        """Check if assignment is currently active"""
        return (
            self.status == ClientAssignmentStatus.ACTIVE and
            (self.expires_at is None or self.expires_at > datetime.utcnow()) and
            self.deactivated_at is None
        )
    
    def deactivate_assignment(self, deactivator_id: int, reason: str) -> bool:
        """Deactivate the client assignment"""
        if self.status != ClientAssignmentStatus.ACTIVE:
            return False
        
        self.status = ClientAssignmentStatus.INACTIVE
        self.deactivated_at = datetime.utcnow()
        self.deactivated_by_id = deactivator_id
        self.deactivation_reason = reason
        return True
    
    def reactivate_assignment(self) -> bool:
        """Reactivate the client assignment"""
        if self.deactivated_at is None:
            return False
        
        self.status = ClientAssignmentStatus.ACTIVE
        self.deactivated_at = None
        self.deactivated_by_id = None
        self.deactivation_reason = None
        return True
    
    # Add unique constraint to prevent duplicate assignments
    __table_args__ = (
        # Index for efficient lookups
        # Note: SQLAlchemy will handle index creation
    )


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    permission_grant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("permission_grants.id"))
    client_assignment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("client_assignments.id"))
    
    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Details and metadata
    details: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    actor: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    permission_grant: Mapped[Optional["PermissionGrant"]] = relationship("PermissionGrant", back_populates="audit_logs")
    client_assignment: Mapped[Optional["ClientAssignment"]] = relationship("ClientAssignment")


class ServiceAccountProperty(Base):
    """Service Account Properties - tracks GA4 properties accessible by each service account"""
    __tablename__ = "service_account_properties"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    
    ga_property_id: Mapped[str] = mapped_column(String(50), nullable=False)
    property_name: Mapped[Optional[str]] = mapped_column(String(255))
    property_account_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    validation_status: Mapped[str] = mapped_column(String(20), default='unknown')  # 'valid', 'invalid', 'unknown'
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    service_account: Mapped["ServiceAccount"] = relationship("ServiceAccount", back_populates="service_account_properties")
    
    # Unique constraint
    __table_args__ = (
        # SQLAlchemy will handle unique constraint creation
    )


class PropertyAccessBinding(Base):
    """Property Access Bindings Cache - caches actual GA4 access bindings"""
    __tablename__ = "property_access_bindings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    
    ga_property_id: Mapped[str] = mapped_column(String(50), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of GA4 roles
    binding_name: Mapped[Optional[str]] = mapped_column(String(500))  # Google's binding resource name
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    synchronized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    service_account: Mapped["ServiceAccount"] = relationship("ServiceAccount", back_populates="property_access_bindings")
    
    # Unique constraint
    __table_args__ = (
        # SQLAlchemy will handle unique constraint creation
    )


class PermissionRequest(Base):
    """Permission request model - handles permission requests before they become grants"""
    __tablename__ = "permission_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # GA4 specific fields
    ga_property_id: Mapped[str] = mapped_column(String(50), nullable=False)
    target_email: Mapped[str] = mapped_column(String(255), nullable=False)
    permission_level: Mapped[PermissionLevel] = mapped_column(Enum(PermissionLevel), nullable=False)
    
    # Request details
    status: Mapped[PermissionRequestStatus] = mapped_column(Enum(PermissionRequestStatus), default=PermissionRequestStatus.PENDING)
    business_justification: Mapped[Optional[str]] = mapped_column(Text)
    requested_duration_days: Mapped[Optional[int]] = mapped_column(Integer)  # Requested duration in days
    
    # Auto-approval tracking
    auto_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval_from_role: Mapped[Optional[UserRole]] = mapped_column(Enum(UserRole))
    
    # Processing details
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    processing_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Conversion to grant
    permission_grant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("permission_grants.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    client: Mapped["Client"] = relationship("Client")
    processed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[processed_by_id])
    permission_grant: Mapped[Optional["PermissionGrant"]] = relationship("PermissionGrant")


class GA4Property(Base):
    """GA4 Property independent entity - Legacy compatible"""
    __tablename__ = "ga4_properties"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # GA4 Property Information
    property_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # properties/123456789
    property_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[str] = mapped_column(String(50), nullable=False)  # accounts/123456
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Property Settings
    website_url: Mapped[Optional[str]] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Seoul")
    currency_code: Mapped[str] = mapped_column(String(3), default="KRW")
    
    # Auto-approval Settings
    auto_approval_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    max_permission_duration_days: Mapped[int] = mapped_column(Integer, default=90)
    
    # Sync Management
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    client: Mapped["Client"] = relationship("Client")
    user_permissions: Mapped[list["UserPermission"]] = relationship(
        "UserPermission", back_populates="ga_property", cascade="all, delete-orphan"
    )
    
    @property
    def needs_sync(self) -> bool:
        """Check if sync is needed (24 hour basis)"""
        if not self.sync_enabled or not self.is_active:
            return False
        
        if not self.last_synced_at:
            return True
        
        return (datetime.utcnow() - self.last_synced_at).total_seconds() > 86400  # 24 hours
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return f"{self.property_name} ({self.property_id})"
    
    def can_auto_approve(self, requested_level: PermissionLevel) -> bool:
        """Check if auto-approval is possible for the requested permission level"""
        if not self.auto_approval_enabled:
            return False
        
        # Only Viewer and Analyst roles can be auto-approved
        auto_approvable_levels = [PermissionLevel.VIEWER, PermissionLevel.ANALYST]
        return requested_level in auto_approvable_levels


class UserPermission(Base):
    """User-Property direct permission mapping - Legacy style"""
    __tablename__ = "user_permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    ga_property_id: Mapped[int] = mapped_column(Integer, ForeignKey("ga4_properties.id"), nullable=False)
    
    # Permission Details
    target_email: Mapped[str] = mapped_column(String(255), nullable=False)
    permission_level: Mapped[PermissionLevel] = mapped_column(Enum(PermissionLevel), nullable=False)
    
    # Lifecycle Management
    status: Mapped[PermissionStatus] = mapped_column(Enum(PermissionStatus), default=PermissionStatus.APPROVED)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Extension Tracking
    extension_count: Mapped[int] = mapped_column(Integer, default=0)
    original_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Revocation Tracking
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # GA4 Integration
    google_permission_id: Mapped[Optional[str]] = mapped_column(String(500))  # Google's permission ID
    synchronized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, synced, failed
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    ga_property: Mapped["GA4Property"] = relationship("GA4Property", back_populates="user_permissions")
    revoked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[revoked_by_id])
    
    @property
    def is_active(self) -> bool:
        """Check if permission is currently active"""
        return (
            self.status == PermissionStatus.APPROVED and
            self.expires_at > datetime.utcnow()
        )
    
    @property
    def days_until_expiry(self) -> int:
        """Days until permission expires"""
        if self.expires_at <= datetime.utcnow():
            return 0
        return (self.expires_at - datetime.utcnow()).days
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if permission expires within 7 days"""
        return 0 <= self.days_until_expiry <= 7
    
    def extend_permission(self, additional_days: int, extender_id: int) -> bool:
        """Extend permission - Legacy style"""
        if not self.is_active:
            return False
        
        self.expires_at = self.expires_at + timedelta(days=additional_days)
        self.extension_count += 1
        self.updated_at = datetime.utcnow()
        return True
    
    def revoke_permission(self, revoker_id: int, reason: str) -> bool:
        """Revoke permission - Legacy style"""
        if self.status != PermissionStatus.APPROVED:
            return False
        
        self.status = PermissionStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_by_id = revoker_id
        self.revocation_reason = reason
        self.updated_at = datetime.utcnow()
        return True


class NotificationLog(Base):
    """Notification log table - Legacy compatible"""
    __tablename__ = "notification_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Reference to audit log
    audit_log_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audit_logs.id"))
    
    # Notification Details
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Message Content
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    message_body: Mapped[Optional[str]] = mapped_column(Text)
    template_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    
    # Delivery Status
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    audit_log: Mapped[Optional["AuditLog"]] = relationship("AuditLog")


class ReportDownloadLog(Base):
    """Report download log - Legacy compatible"""
    __tablename__ = "report_download_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # User Information
    admin_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report Information
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    report_id: Mapped[str] = mapped_column(String(255), nullable=False)
    report_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_format: Mapped[str] = mapped_column(String(10), default="json")  # json, csv, excel
    
    # Download Details
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # File Information
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relationships
    admin: Mapped["User"] = relationship("User")


class PropertyAccessRequest(Base):
    """Enhanced property access request model with comprehensive workflow"""
    __tablename__ = "property_access_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    ga4_property_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ga4_properties.id"))
    requested_property_id: Mapped[str] = mapped_column(String(50), nullable=False)  # GA4 property ID string
    
    # Request details
    status: Mapped[PropertyAccessStatus] = mapped_column(Enum(PropertyAccessStatus), default=PropertyAccessStatus.REQUESTED)
    permission_level: Mapped[PermissionLevel] = mapped_column(Enum(PermissionLevel), nullable=False)
    target_email: Mapped[str] = mapped_column(String(255), nullable=False)
    business_justification: Mapped[str] = mapped_column(Text, nullable=False)
    requested_duration_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    # Auto-approval settings
    auto_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval_from_role: Mapped[Optional[UserRole]] = mapped_column(Enum(UserRole))
    
    # Processing information
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    processing_notes: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Approval workflow
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Revocation tracking
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    priority_level: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel), default=PriorityLevel.NORMAL)
    external_ticket_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="property_access_requests", foreign_keys=[user_id])
    client: Mapped["Client"] = relationship("Client")
    ga4_property: Mapped[Optional["GA4Property"]] = relationship("GA4Property")
    processed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[processed_by_id])
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])
    revoked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[revoked_by_id])
    
    @property
    def is_active(self) -> bool:
        """Check if access request is currently active"""
        return (
            self.status == PropertyAccessStatus.APPROVED and
            (self.expires_at is None or self.expires_at > datetime.utcnow())
        )
    
    @property
    def days_until_expiry(self) -> int:
        """Days until access expires"""
        if not self.expires_at or self.expires_at <= datetime.utcnow():
            return 0
        return (self.expires_at - datetime.utcnow()).days
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if access expires within 7 days"""
        return self.expires_at and 0 <= self.days_until_expiry <= 7
    
    def approve_request(self, approver_id: int, duration_days: int = None) -> bool:
        """Approve the access request"""
        if self.status != PropertyAccessStatus.REQUESTED:
            return False
        
        self.status = PropertyAccessStatus.APPROVED
        self.approved_at = datetime.utcnow()
        self.approved_by_id = approver_id
        
        # Set expiration date
        duration = duration_days or self.requested_duration_days
        self.expires_at = datetime.utcnow() + timedelta(days=duration)
        
        return True
    
    def deny_request(self, processor_id: int, reason: str) -> bool:
        """Deny the access request"""
        if self.status != PropertyAccessStatus.REQUESTED:
            return False
        
        self.status = PropertyAccessStatus.DENIED
        self.processed_at = datetime.utcnow()
        self.processed_by_id = processor_id
        self.rejection_reason = reason
        
        return True
    
    def revoke_access(self, revoker_id: int, reason: str) -> bool:
        """Revoke approved access"""
        if self.status != PropertyAccessStatus.APPROVED:
            return False
        
        self.status = PropertyAccessStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_by_id = revoker_id
        self.revocation_reason = reason
        
        return True


class UserActivityLog(Base):
    """Comprehensive user activity audit log"""
    __tablename__ = "user_activity_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))  # For admin actions on other users
    client_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clients.id"))
    property_access_request_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("property_access_requests.id"))
    
    # Activity details
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # Support IPv4 and IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Additional metadata
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)  # How long the action took
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_activity_logs", foreign_keys=[user_id])
    target_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[target_user_id])
    client: Mapped[Optional["Client"]] = relationship("Client")
    property_access_request: Mapped[Optional["PropertyAccessRequest"]] = relationship("PropertyAccessRequest")


class UserSession(Base):
    """User session tracking with security features"""
    __tablename__ = "user_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relationships
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    session_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Security tracking
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # Support IPv4 and IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Session lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Logout tracking
    logged_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    logout_reason: Mapped[Optional[str]] = mapped_column(String(50))  # 'user_logout', 'timeout', 'admin_revoke', 'security'
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_sessions")
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return self.expires_at <= datetime.utcnow()
    
    @property
    def time_until_expiry(self) -> timedelta:
        """Time until session expires"""
        return max(timedelta(0), self.expires_at - datetime.utcnow())
    
    def extend_session(self, additional_hours: int = 24) -> bool:
        """Extend session expiration"""
        if not self.is_active or self.is_expired:
            return False
        
        self.expires_at = datetime.utcnow() + timedelta(hours=additional_hours)
        self.last_activity_at = datetime.utcnow()
        return True
    
    def terminate_session(self, reason: str = "user_logout") -> bool:
        """Terminate the session"""
        if not self.is_active:
            return False
        
        self.is_active = False
        self.logged_out_at = datetime.utcnow()
        self.logout_reason = reason
        return True