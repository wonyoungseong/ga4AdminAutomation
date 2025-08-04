"""
Pydantic schemas for API requests and responses
"""

from datetime import datetime
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .db_models import (
    UserRole, UserStatus, PermissionLevel, PermissionStatus, 
    ClientAssignmentStatus, PermissionRequestStatus,
    NotificationChannel, NotificationStatus, ReportType
)


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


# Authentication schemas
class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    """User creation request schema"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8)


class UserResponse(BaseSchema):
    """User response schema"""
    id: int
    email: str
    name: str
    company: Optional[str] = None
    role: UserRole
    status: UserStatus
    is_representative: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# User management schemas
class UserUpdate(BaseModel):
    """User update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_representative: Optional[bool] = None


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset schema"""
    token: str
    new_password: str = Field(..., min_length=8)


# Client schemas
class ClientCreate(BaseModel):
    """Client creation request schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None


class ClientUpdate(BaseModel):
    """Client update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseSchema):
    """Client response schema"""
    id: int
    name: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Service Account schemas
class ServiceAccountCreate(BaseModel):
    """Service account creation request schema"""
    client_id: int
    email: EmailStr
    secret_name: str = Field(..., min_length=1)
    display_name: Optional[str] = Field(None, max_length=100)
    project_id: Optional[str] = Field(None, max_length=255)
    credentials_json: Optional[str] = None  # For validation during creation


class ServiceAccountUpdate(BaseModel):
    """Service account update request schema"""
    display_name: Optional[str] = Field(None, max_length=100)
    secret_name: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class ServiceAccountResponse(BaseSchema):
    """Service account response schema"""
    id: int
    client_id: int
    email: str
    display_name: Optional[str] = None
    project_id: Optional[str] = None
    is_active: bool
    health_status: str
    health_checked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    key_version: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Permission Grant schemas
class PermissionGrantCreate(BaseModel):
    """Permission grant creation request schema"""
    client_id: int
    service_account_id: int
    ga_property_id: str = Field(..., min_length=1)
    target_email: EmailStr
    permission_level: PermissionLevel
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None


class PermissionGrantUpdate(BaseModel):
    """Permission grant update request schema"""
    permission_level: Optional[PermissionLevel] = None
    status: Optional[PermissionStatus] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class PermissionGrantResponse(BaseSchema):
    """Permission grant response schema"""
    id: int
    user_id: int
    client_id: int
    service_account_id: int
    ga_property_id: str
    target_email: str
    permission_level: PermissionLevel
    status: PermissionStatus
    expires_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Audit Log schemas
class AuditLogResponse(BaseSchema):
    """Audit log response schema"""
    id: int
    actor_id: Optional[int] = None
    permission_grant_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


# Notification schemas
class NotificationCreate(BaseModel):
    """Notification creation request schema"""
    recipient_email: EmailStr
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    notification_type: str = "info"


class NotificationResponse(BaseSchema):
    """Notification response schema"""
    id: int
    recipient_email: str
    subject: str
    message: str
    notification_type: str
    sent_at: Optional[datetime] = None
    created_at: datetime


# Common response schemas
class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str


# Client Assignment schemas
class ClientAssignmentCreate(BaseModel):
    """Client assignment creation request schema"""
    user_id: int
    client_id: int
    status: ClientAssignmentStatus = ClientAssignmentStatus.ACTIVE
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class ClientAssignmentBulkCreate(BaseModel):
    """Bulk client assignment creation request schema"""
    user_ids: List[int] = Field(..., min_items=1)
    client_ids: List[int] = Field(..., min_items=1)
    status: ClientAssignmentStatus = ClientAssignmentStatus.ACTIVE
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class ClientAssignmentUpdate(BaseModel):
    """Client assignment update request schema"""
    status: Optional[ClientAssignmentStatus] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class ClientAssignmentResponse(BaseSchema):
    """Client assignment response schema"""
    id: int
    user_id: int
    client_id: int
    assigned_by_id: int
    status: ClientAssignmentStatus
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested objects (optional for different endpoint needs)
    user: Optional[UserResponse] = None
    client: Optional[ClientResponse] = None
    assigned_by: Optional[UserResponse] = None


class UserWithClientsResponse(UserResponse):
    """User response with assigned clients"""
    assigned_clients: List[ClientAssignmentResponse] = []
    total_assigned_clients: int = 0


class ClientWithUsersResponse(ClientResponse):
    """Client response with assigned users"""
    assigned_users: List[ClientAssignmentResponse] = []
    total_assigned_users: int = 0


class AccessControlSummary(BaseModel):
    """Access control summary for a user"""
    user_id: int
    accessible_client_ids: List[int]
    role_based_access: bool
    assignment_based_access: List[int]


T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


# GA4 Property schemas
class GA4PropertyResponse(BaseSchema):
    """GA4 Property response schema"""
    id: str
    name: str
    account_id: str
    service_account_id: int
    is_active: bool
    discovered_at: datetime
    validation_status: str
    last_validated_at: Optional[datetime] = None


# Service Account Property schemas
class ServiceAccountPropertyResponse(BaseSchema):
    """Service Account Property response schema"""
    id: int
    service_account_id: int
    ga_property_id: str
    property_name: Optional[str] = None
    property_account_id: Optional[str] = None
    is_active: bool
    discovered_at: datetime
    last_validated_at: Optional[datetime] = None
    validation_status: str
    created_at: datetime
    updated_at: datetime


# Property Access Binding schemas
class PropertyAccessBindingResponse(BaseSchema):
    """Property Access Binding response schema"""
    id: int
    service_account_id: int
    ga_property_id: str
    user_email: str
    roles: List[str]
    binding_name: Optional[str] = None
    is_active: bool
    synchronized_at: datetime
    created_at: datetime
    updated_at: datetime


# Additional response schemas
class MessageResponse(BaseModel):
    """Simple message response schema"""
    message: str
    

class HealthStatusResponse(BaseModel):
    """Health status response schema"""
    service_account_id: int
    email: str
    health_status: str
    health_checked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    

class ValidationResultResponse(BaseModel):
    """Validation result response schema"""
    service_account_id: int
    email: str
    is_valid: bool
    has_ga4_access: bool
    accessible_accounts: List[dict]
    accessible_properties: List[dict]
    errors: List[str]
    validated_at: str


# Permission Request schemas
class PermissionRequestCreate(BaseModel):
    """Permission request creation schema"""
    client_id: int = Field(..., gt=0, description="Client ID that the user is assigned to")
    ga_property_id: str = Field(..., min_length=1, description="GA4 Property ID to request access to")
    target_email: EmailStr = Field(..., description="Email address to grant permission to")
    permission_level: PermissionLevel = Field(..., description="Requested permission level")
    business_justification: Optional[str] = Field(None, max_length=1000, description="Business justification for the access")
    requested_duration_days: Optional[int] = Field(None, gt=0, le=365, description="Requested access duration in days")


class PermissionRequestUpdate(BaseModel):
    """Permission request update schema"""
    status: Optional[PermissionRequestStatus] = None
    processing_notes: Optional[str] = Field(None, max_length=1000)


class PermissionRequestResponse(BaseSchema):
    """Permission request response schema"""
    id: int
    user_id: int
    client_id: int
    ga_property_id: str
    target_email: str
    permission_level: PermissionLevel
    status: PermissionRequestStatus
    business_justification: Optional[str] = None
    requested_duration_days: Optional[int] = None
    auto_approved: bool
    requires_approval_from_role: Optional[UserRole] = None
    processed_at: Optional[datetime] = None
    processed_by_id: Optional[int] = None
    processing_notes: Optional[str] = None
    permission_grant_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    user: Optional[UserResponse] = None
    client: Optional[ClientResponse] = None
    processed_by: Optional[UserResponse] = None


class PermissionRequestWithPropertyResponse(PermissionRequestResponse):
    """Permission request with property details"""
    property_name: Optional[str] = None
    service_account_email: Optional[str] = None


class ClientPropertiesResponse(BaseModel):
    """Client with available GA4 properties response schema"""
    client_id: int
    client_name: str
    service_accounts: List["ServiceAccountWithPropertiesResponse"]
    total_properties: int


class ServiceAccountWithPropertiesResponse(BaseModel):
    """Service account with properties response schema"""
    id: int
    email: str
    display_name: Optional[str] = None
    is_active: bool
    health_status: str
    properties: List[ServiceAccountPropertyResponse]


class AutoApprovalRuleResponse(BaseModel):
    """Auto approval rule evaluation response"""
    permission_level: PermissionLevel
    user_role: UserRole
    auto_approved: bool
    requires_approval_from_role: Optional[UserRole] = None
    reason: str


# ===== Legacy Extension Schemas =====

# GA4 Property schemas
class GA4PropertyCreate(BaseModel):
    """GA4 Property creation schema"""
    client_id: int = Field(..., gt=0)
    property_id: str = Field(..., pattern=r'^properties/\d+$', description="GA4 Property ID (e.g., properties/123456789)")
    property_name: str = Field(..., min_length=1, max_length=255)
    account_id: str = Field(..., pattern=r'^accounts/\d+$', description="GA4 Account ID (e.g., accounts/123456)")
    account_name: str = Field(..., min_length=1, max_length=255)
    website_url: Optional[str] = Field(None, max_length=500)
    timezone: str = Field("Asia/Seoul", max_length=50)
    currency_code: str = Field("KRW", min_length=3, max_length=3)
    auto_approval_enabled: bool = Field(False)
    max_permission_duration_days: int = Field(90, ge=1, le=365)


class GA4PropertyUpdate(BaseModel):
    """GA4 Property update schema"""
    property_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    website_url: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None
    sync_enabled: Optional[bool] = None
    auto_approval_enabled: Optional[bool] = None
    max_permission_duration_days: Optional[int] = Field(None, ge=1, le=365)


class GA4PropertyResponse(BaseSchema):
    """GA4 Property response schema"""
    id: int
    client_id: int
    property_id: str
    property_name: str
    account_id: str
    account_name: str
    website_url: Optional[str] = None
    timezone: str
    currency_code: str
    auto_approval_enabled: bool
    max_permission_duration_days: int
    is_active: bool
    sync_enabled: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    display_name: Optional[str] = None
    needs_sync: Optional[bool] = None
    
    # Nested objects
    client: Optional[ClientResponse] = None


# User Permission schemas
class UserPermissionCreate(BaseModel):
    """User Permission creation schema"""
    user_id: int = Field(..., gt=0)
    ga_property_id: int = Field(..., gt=0)
    target_email: EmailStr
    permission_level: PermissionLevel
    expires_at: datetime


class UserPermissionResponse(BaseSchema):
    """User Permission response schema"""
    id: int
    user_id: int
    ga_property_id: int
    target_email: str
    permission_level: PermissionLevel
    status: PermissionStatus
    granted_at: datetime
    expires_at: datetime
    extension_count: int
    original_expires_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by_id: Optional[int] = None
    revocation_reason: Optional[str] = None
    google_permission_id: Optional[str] = None
    synchronized_at: Optional[datetime] = None
    sync_status: str
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_active: Optional[bool] = None
    days_until_expiry: Optional[int] = None
    is_expiring_soon: Optional[bool] = None
    
    # Nested objects
    user: Optional[UserResponse] = None
    ga_property: Optional[GA4PropertyResponse] = None
    revoked_by: Optional[UserResponse] = None


# Permission Extension schemas
class PermissionExtensionRequest(BaseModel):
    """Permission extension request schema"""
    additional_days: int = Field(..., ge=1, le=90, description="Additional days to extend (1-90)")
    reason: str = Field(..., min_length=10, max_length=500, description="Extension reason")


class PermissionRevocationRequest(BaseModel):
    """Permission revocation request schema"""
    reason: str = Field(..., min_length=10, max_length=500, description="Revocation reason")
    immediate: bool = Field(False, description="Whether to revoke immediately")


# Notification schemas
class NotificationLogResponse(BaseSchema):
    """Notification log response schema"""
    id: int
    audit_log_id: Optional[int] = None
    channel: NotificationChannel
    recipient: str
    template_type: str
    subject: Optional[str] = None
    message_body: Optional[str] = None
    template_data: Optional[str] = None
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime


# Report Download schemas
class ReportDownloadLogResponse(BaseSchema):
    """Report download log response schema"""
    id: int
    admin_id: int
    report_type: ReportType
    report_id: str
    report_name: Optional[str] = None
    file_format: str
    downloaded_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_path: Optional[str] = None
    
    # Nested objects
    admin: Optional[UserResponse] = None


# System Metrics schemas
class SystemMetricsResponse(BaseModel):
    """System metrics response schema"""
    total_users: int
    active_users: int
    pending_registrations: int
    total_permissions: int
    active_permissions: int
    expired_permissions: int
    expiring_soon_permissions: int  # Within 7 days
    total_clients: int
    active_clients: int
    total_properties: int
    active_properties: int
    daily_logins: int
    failed_logins: int
    generated_at: datetime


# Enhanced Permission Grant schemas with lifecycle methods
class PermissionGrantExtended(PermissionGrantResponse):
    """Enhanced Permission Grant with lifecycle properties"""
    extension_count: int
    original_expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_by_id: Optional[int] = None
    revocation_reason: Optional[str] = None
    
    # Computed properties
    is_active: Optional[bool] = None
    days_until_expiry: Optional[int] = None
    is_expiring_soon: Optional[bool] = None
    can_extend: Optional[bool] = None
    
    # Nested objects
    revoked_by: Optional[UserResponse] = None