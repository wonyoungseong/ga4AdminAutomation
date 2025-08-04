#!/usr/bin/env python3
"""
Simple server start for testing without database setup
"""

import sys
import asyncio
import enum
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from functools import wraps
from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import hashlib
import secrets
import jwt
from ga4_api_client import GA4ApiClient, map_permission_to_ga4_roles
from email_service import email_service
from fastapi import Request

# Add src to path
sys.path.append('/Users/seong-won-yeong/Dev/ga4AdminAutomation/backend')

# Security
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# JWT 설정
SECRET_KEY = "GA4_ADMIN_SECRET_KEY_2024"  # 실제 배포시에는 환경변수로 관리
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# GA4 API 클라이언트 초기화
ga4_client = GA4ApiClient('ga4-service-account.json')

# ============= RBAC (Role-Based Access Control) System =============

# 권한 승인 규칙 정의
PERMISSION_APPROVAL_RULES = {
    "Viewer": {
        "auto_approve_for": ["Requester"],  # Requester가 요청하면 자동 승인
        "requires_approval_from": "Admin"   # 그 외에는 Admin 승인 필요
    },
    "Editor": {
        "auto_approve_for": [],  # 자동 승인 없음
        "requires_approval_from": "Admin"  # Admin 승인 필요
    },
    "Marketer": {
        "auto_approve_for": [],
        "requires_approval_from": "Admin"
    },
    "Administrator": {
        "auto_approve_for": [],
        "requires_approval_from": "Super Admin"  # Super Admin 승인 필요
    }
}

def get_required_approver_role(permission_type: str, requester_role: str) -> str:
    """권한 타입과 요청자 역할에 따른 승인자 역할 반환"""
    rules = PERMISSION_APPROVAL_RULES.get(permission_type, {})
    
    # 자동 승인 대상인지 확인
    if requester_role in rules.get("auto_approve_for", []):
        return "auto"
    
    # 필요한 승인자 역할 반환
    return rules.get("requires_approval_from", "Super Admin")

def can_approve_permission(approver_role: str, permission_type: str, requester_role: str) -> bool:
    """승인자가 해당 권한을 승인할 수 있는지 확인"""
    required_approver = get_required_approver_role(permission_type, requester_role)
    
    if required_approver == "auto":
        return True  # 자동 승인 가능
    
    # 역할 계층 확인
    role_levels = {"Viewer": 1, "Requester": 2, "Admin": 3, "Super Admin": 4}
    approver_level = role_levels.get(approver_role, 0)
    required_level = role_levels.get(required_approver, 5)
    
    return approver_level >= required_level

# 역할 계층 구조 정의
ROLE_HIERARCHY = {
    "Super Admin": ["Super Admin", "Admin", "Requester", "Viewer"],
    "Admin": ["Admin", "Requester", "Viewer"], 
    "Requester": ["Requester", "Viewer"],
    "Viewer": ["Viewer"]
}

# 역할별 권한 매트릭스 (Client Assignment 권한 포함)
ROLE_PERMISSIONS = {
    "Super Admin": [
        "create_user", "read_user", "update_user", "delete_user", "change_user_role",
        "create_client", "read_client", "update_client", "delete_client",
        "manage_client_assignments", "read_all_client_assignments",
        "read_permission", "approve_permission", "reject_permission", "create_permission", "delete_permission",
        "read_audit_log", "read_all_audit_logs",
        "ga4_admin", "system_admin"
    ],
    "Admin": [
        "create_user", "read_user", "update_user", "delete_user",  # Cannot change Super Admin roles
        "create_client", "read_client", "update_client", "delete_client",
        "manage_client_assignments", "read_assigned_client_assignments",
        "read_permission", "approve_permission", "reject_permission", "create_permission", "delete_permission",
        "read_audit_log", "read_filtered_audit_logs",
        "ga4_admin"
    ],
    "Requester": [
        "read_user", "update_own_profile",
        "read_client", "read_assigned_clients", "read_own_client_assignments",
        "create_permission", "read_own_permissions",
        "read_own_audit_logs"
    ],
    "Viewer": [
        "read_user", "update_own_profile",
        "read_client", "read_assigned_clients", "read_own_client_assignments",
        "read_permissions",  # View only
        "read_own_audit_logs"
    ]
}

def has_permission(user_role: str, permission: str) -> bool:
    """사용자 역할이 특정 권한을 가지고 있는지 확인"""
    return permission in ROLE_PERMISSIONS.get(user_role, [])

def can_manage_user_role(manager_role: str, target_role: str) -> bool:
    """매니저가 대상 역할을 관리할 수 있는지 확인"""
    if manager_role == "Super Admin":
        return True
    elif manager_role == "Admin":
        return target_role not in ["Super Admin", "Admin"]
    return False

def can_access_user(current_user_role: str, current_user_id: int, target_user_id: int) -> bool:
    """사용자가 다른 사용자 정보에 접근할 수 있는지 확인"""
    if current_user_role in ["Super Admin", "Admin"]:
        return True
    return current_user_id == target_user_id

# ============= Client Assignment Helper Functions =============

def get_user_accessible_clients(user_id: int, user_role: str) -> List[int]:
    """사용자가 접근 가능한 클라이언트 ID 목록 반환"""
    # Super Admin은 모든 활성 클라이언트에 접근 가능
    if user_role == "Super Admin":
        return [c.id for c in clients_db if c.is_active]
    
    # Admin도 모든 활성 클라이언트에 접근 가능 (비즈니스 규칙에 따라 변경 가능)
    elif user_role == "Admin":
        return [c.id for c in clients_db if c.is_active]
    
    # Requester와 Viewer는 할당된 클라이언트만 접근 가능
    else:
        return [
            assignment.client_id 
            for assignment in client_assignments_db 
            if assignment.user_id == user_id and assignment.status == "active"
        ]

def check_user_client_access(user_id: int, client_id: int, user_role: str) -> bool:
    """사용자가 특정 클라이언트에 접근 가능한지 확인"""
    # Super Admin은 모든 활성 클라이언트에 접근 가능
    if user_role == "Super Admin":
        client = next((c for c in clients_db if c.id == client_id), None)
        return client is not None and client.is_active
    
    # Admin도 모든 활성 클라이언트에 접근 가능
    elif user_role == "Admin":
        client = next((c for c in clients_db if c.id == client_id), None)
        return client is not None and client.is_active
    
    # Requester와 Viewer는 할당 확인 필요
    else:
        assignment = next(
            (a for a in client_assignments_db 
             if a.user_id == user_id and a.client_id == client_id and a.status == "active"), 
            None
        )
        return assignment is not None

def get_user_assignments_by_id(user_id: int, include_inactive: bool = False):
    """사용자의 클라이언트 할당 목록 조회"""
    assignments = [a for a in client_assignments_db if a.user_id == user_id]
    
    if not include_inactive:
        assignments = [a for a in assignments if a.status == "active"]
    
    return assignments

def get_client_assignments_by_id(client_id: int, include_inactive: bool = False):
    """클라이언트의 사용자 할당 목록 조회"""
    assignments = [a for a in client_assignments_db if a.client_id == client_id]
    
    if not include_inactive:
        assignments = [a for a in assignments if a.status == "active"]
    
    return assignments

def get_access_control_summary(user_id: int, user_role: str):
    """사용자의 접근 제어 요약 정보 조회"""
    accessible_clients = get_user_accessible_clients(user_id, user_role)
    assignment_based = [
        a.client_id for a in client_assignments_db 
        if a.user_id == user_id and a.status == "active"
    ]
    
    return {
        "user_id": user_id,
        "accessible_client_ids": accessible_clients,
        "role_based_access": user_role in ["Super Admin", "Admin"],
        "assignment_based_access": assignment_based
    }

# 클라이언트 접근 제어 데코레이터
def require_client_access(func: Callable):
    """클라이언트 접근 권한을 확인하는 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('user')
        client_id = kwargs.get('client_id')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if client_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client ID required"
            )
        
        # 사용자 role이 dict 형태이거나 객체 형태일 때 처리
        if isinstance(current_user, dict):
            user_role = current_user.get("role")
            user_id = current_user.get("id")
        else:
            user_role = getattr(current_user, "role", None)
            user_id = getattr(current_user, "id", None)
        
        if not check_user_client_access(user_id, client_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to client {client_id}"
            )
        
        return await func(*args, **kwargs)
    return wrapper

# 권한 데코레이터
def require_permissions(required_permissions: List[str]):
    """API 엔드포인트에 필요한 권한을 검사하는 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 현재 사용자 가져오기 (kwargs에서 user 파라미터 찾기)
            current_user = kwargs.get('user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 사용자 role이 dict 형태이거나 객체 형태일 때 처리
            if isinstance(current_user, dict):
                user_role = current_user.get("role")
                user_dict = current_user
            else:
                user_role = getattr(current_user, "role", None)
                # UserInDB 객체를 dict로 변환해서 함수에 전달
                user_dict = {
                    "id": getattr(current_user, "id", None),
                    "email": getattr(current_user, "email", None),
                    "name": getattr(current_user, "name", None),
                    "role": user_role,
                    "is_active": getattr(current_user, "is_active", None)
                }
                kwargs['user'] = user_dict
            
            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User role not found"
                )
            
            # 권한 검사
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])
            missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
            
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(allowed_roles: List[str]):
    """특정 역할만 접근할 수 있도록 제한하는 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for key, value in kwargs.items():
                if hasattr(value, 'role') and hasattr(value, 'email'):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 패스워드 해싱 함수
def hash_password(password: str) -> str:
    """패스워드를 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """패스워드 검증"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except jwt.PyJWTError:
        return None

# 감사 로그 자동 생성 함수 (클래스 정의 후에 구현)

# Client Assignment Models
class ClientAssignmentStatus(str, enum.Enum):
    """Client assignment status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class ClientAssignment(BaseModel):
    id: int
    user_id: int
    client_id: int
    assigned_by_id: int
    status: str
    assigned_at: str
    expires_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str

class CreateClientAssignmentRequest(BaseModel):
    user_id: int
    client_id: int
    status: str = "active"
    expires_at: Optional[str] = None
    notes: Optional[str] = None

class UpdateClientAssignmentRequest(BaseModel):
    status: Optional[str] = None
    expires_at: Optional[str] = None
    notes: Optional[str] = None

class BulkAssignmentRequest(BaseModel):
    user_ids: List[int]
    client_ids: List[int]
    status: str = "active"
    expires_at: Optional[str] = None
    notes: Optional[str] = None

class AccessControlSummary(BaseModel):
    user_id: int
    accessible_client_ids: List[int]
    role_based_access: bool
    assignment_based_access: List[int]

# Data Models
class PropertyPermission(BaseModel):
    property_id: str
    property_name: str
    current_permission: str
    requested_permission: str

class Permission(BaseModel):
    id: int
    requester_email: str
    requester_name: str
    client_name: str
    properties: List[PropertyPermission]
    status: str
    requested_at: str
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None

class CreatePermissionRequest(BaseModel):
    requester_email: str
    client_name: str
    properties: List[PropertyPermission]
    notes: Optional[str] = None

class UpdatePermissionRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class User(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class UserInDB(User):
    password_hash: str

class CreateUserRequest(BaseModel):
    email: str
    name: str
    role: str
    password: str

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class Client(BaseModel):
    id: int
    name: str
    company_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    ga4_property_id: str
    is_active: bool
    created_at: str
    last_updated: str
    user_count: int
    description: Optional[str] = None

class CreateClientRequest(BaseModel):
    name: str
    company_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    ga4_property_id: str
    description: Optional[str] = None

class UpdateClientRequest(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    ga4_property_id: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class AuditLog(BaseModel):
    id: int
    action: str
    user_email: str
    user_name: str
    target_type: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    ip_address: str
    user_agent: str
    timestamp: str
    details: Optional[str] = None
    status: str  # "success", "failure", "warning"

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

# Mock Database - 실제 해시된 패스워드 포함
users_db: List[UserInDB] = [
    UserInDB(
        id=1,
        email="admin@example.com",
        name="시스템 관리자",
        role="Super Admin",
        is_active=True,
        created_at="2024-01-01T00:00:00Z",
        last_login="2024-01-20T10:30:00Z",
        password_hash=hash_password("admin123")  # admin123
    ),
    UserInDB(
        id=2,
        email="manager@example.com",
        name="김매니저",
        role="Admin",
        is_active=True,
        created_at="2024-01-05T00:00:00Z",
        last_login="2024-01-20T09:15:00Z",
        password_hash=hash_password("manager123")  # manager123
    ),
    UserInDB(
        id=3,
        email="user@example.com",
        name="이사용자",
        role="Requester",
        is_active=True,
        created_at="2024-01-10T00:00:00Z",
        last_login="2024-01-19T16:45:00Z",
        password_hash=hash_password("user123")  # user123
    ),
    UserInDB(
        id=4,
        email="viewer@example.com",
        name="박뷰어",
        role="Viewer",
        is_active=False,
        created_at="2024-01-15T00:00:00Z",
        last_login="2024-01-18T14:20:00Z",
        password_hash=hash_password("viewer123")  # viewer123
    ),
    UserInDB(
        id=5,
        email="activeviewer@example.com",
        name="활성뷰어",
        role="Viewer",
        is_active=True,
        created_at="2024-01-20T00:00:00Z",
        last_login="2024-01-20T14:20:00Z",
        password_hash=hash_password("viewer123")  # viewer123
    )
]

clients_db: List[Client] = [
    Client(
        id=1,
        name="ABC 마케팅",
        company_name="ABC 회사",
        contact_email="contact@abc.com",
        contact_phone="02-1234-5678",
        ga4_property_id="GA_123456789",
        is_active=True,
        created_at="2024-01-01T00:00:00Z",
        last_updated="2024-01-20T10:30:00Z",
        user_count=5,
        description="온라인 마케팅 서비스 제공업체"
    ),
    Client(
        id=2,
        name="XYZ 이커머스",
        company_name="XYZ 기업",
        contact_email="admin@xyz.com",
        contact_phone="02-9876-5432",
        ga4_property_id="GA_987654321",
        is_active=True,
        created_at="2024-01-05T00:00:00Z",
        last_updated="2024-01-19T14:20:00Z",
        user_count=8,
        description="온라인 쇼핑몰 운영"
    ),
    Client(
        id=3,
        name="DEF 테크",
        company_name="DEF 스타트업",
        contact_email="hello@def.tech",
        ga4_property_id="GA_456789123",
        is_active=False,
        created_at="2024-01-10T00:00:00Z",
        last_updated="2024-01-18T09:15:00Z",
        user_count=3,
        description="모바일 앱 개발 스타트업"
    ),
    Client(
        id=4,
        name="GHI 솔루션",
        company_name="GHI 솔루션즈",
        contact_email="support@ghi.solutions",
        contact_phone="02-5555-7777",
        ga4_property_id="GA_789123456",
        is_active=True,
        created_at="2024-01-15T00:00:00Z",
        last_updated="2024-01-20T16:45:00Z",
        user_count=12,
        description="기업용 소프트웨어 솔루션"
    )
]

# Client Assignments Mock Database
client_assignments_db: List[ClientAssignment] = [
    ClientAssignment(
        id=1,
        user_id=3,  # user@example.com (Requester)
        client_id=1,  # ABC 마케팅
        assigned_by_id=1,  # admin@example.com
        status="active",
        assigned_at="2024-01-15T10:00:00Z",
        expires_at=None,
        notes="초기 클라이언트 할당",
        created_at="2024-01-15T10:00:00Z",
        updated_at="2024-01-15T10:00:00Z"
    ),
    ClientAssignment(
        id=2,
        user_id=3,  # user@example.com (Requester)
        client_id=2,  # XYZ 이커머스
        assigned_by_id=2,  # manager@example.com
        status="active",
        assigned_at="2024-01-16T14:30:00Z",
        expires_at=None,
        notes="추가 클라이언트 할당",
        created_at="2024-01-16T14:30:00Z",
        updated_at="2024-01-16T14:30:00Z"
    ),
    ClientAssignment(
        id=3,
        user_id=5,  # activeviewer@example.com (Viewer)
        client_id=1,  # ABC 마케팅
        assigned_by_id=1,  # admin@example.com
        status="active",
        assigned_at="2024-01-18T09:15:00Z",
        expires_at=None,
        notes="뷰어 권한으로 할당",
        created_at="2024-01-18T09:15:00Z",
        updated_at="2024-01-18T09:15:00Z"
    ),
    ClientAssignment(
        id=4,
        user_id=4,  # viewer@example.com (Viewer - Inactive)
        client_id=3,  # DEF 테크
        assigned_by_id=2,  # manager@example.com
        status="inactive",
        assigned_at="2024-01-10T16:45:00Z",
        expires_at="2024-01-20T00:00:00Z",
        notes="비활성화된 할당",
        created_at="2024-01-10T16:45:00Z",
        updated_at="2024-01-19T12:00:00Z"
    )
]

audit_logs_db: List[AuditLog] = [
    AuditLog(
        id=1,
        action="login",
        user_email="admin@example.com",
        user_name="시스템 관리자",
        target_type="user",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        timestamp="2024-01-20T10:30:00Z",
        status="success",
        details="성공적으로 로그인함"
    ),
    AuditLog(
        id=2,
        action="create_user",
        user_email="admin@example.com",
        user_name="시스템 관리자",
        target_type="user",
        target_id="123",
        target_name="새사용자@example.com",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        timestamp="2024-01-20T09:15:00Z",
        status="success",
        details="새 사용자 계정 생성"
    ),
    AuditLog(
        id=3,
        action="approve_permission",
        user_email="manager@example.com",
        user_name="김매니저",
        target_type="permission",
        target_id="456",
        target_name="GA4 뷰어 권한",
        ip_address="192.168.1.101",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        timestamp="2024-01-20T08:45:00Z",
        status="success",
        details="권한 요청 승인 처리"
    ),
    AuditLog(
        id=4,
        action="login",
        user_email="user@example.com",
        user_name="이사용자",
        target_type="user",
        ip_address="192.168.1.102",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
        timestamp="2024-01-20T07:30:00Z",
        status="failure",
        details="잘못된 비밀번호로 로그인 실패"
    ),
    AuditLog(
        id=5,
        action="delete_client",
        user_email="admin@example.com",
        user_name="시스템 관리자",
        target_type="client",
        target_id="789",
        target_name="테스트 클라이언트",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        timestamp="2024-01-19T16:20:00Z",
        status="success",
        details="테스트용 클라이언트 삭제"
    ),
    AuditLog(
        id=6,
        action="update_permission",
        user_email="manager@example.com",
        user_name="김매니저",
        target_type="permission",
        target_id="321",
        target_name="GA4 편집 권한",
        ip_address="192.168.1.101",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        timestamp="2024-01-19T14:15:00Z",
        status="warning",
        details="권한 변경 시 경고 발생"
    )
]

# 감사 로그 자동 생성 함수
def create_audit_log(
    action: str,
    user,  # UserInDB 객체 또는 dict
    target_type: str,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    details: Optional[str] = None,
    status: str = "success",
    request: Optional[Request] = None
):
    """감사 로그 자동 생성"""
    global audit_logs_db
    
    # IP 주소 및 User Agent 추출
    ip_address = "127.0.0.1"
    user_agent = "Unknown"
    
    if request:
        ip_address = request.client.host if request.client else "127.0.0.1"
        user_agent = request.headers.get("user-agent", "Unknown")
    
    new_id = max([log.id for log in audit_logs_db], default=0) + 1
    
    # user가 dict인지 UserInDB 객체인지 확인
    if isinstance(user, dict):
        user_email = user.get("email", "unknown")
        user_name = user.get("name", "unknown")
    else:
        user_email = user.email
        user_name = user.name
    
    audit_log = AuditLog(
        id=new_id,
        action=action,
        user_email=user_email,
        user_name=user_name,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now().isoformat() + "Z",
        details=details,
        status=status
    )
    
    audit_logs_db.append(audit_log)
    return audit_log

permissions_db: List[Permission] = [
    Permission(
        id=1,
        requester_email="user@example.com",
        requester_name="이사용자",
        client_name="ABC 회사",
        properties=[
            PropertyPermission(
                property_id="GA_123456789",
                property_name="ABC 웹사이트",
                current_permission="None",
                requested_permission="Viewer"
            ),
            PropertyPermission(
                property_id="GA_123456790", 
                property_name="ABC 모바일앱",
                current_permission="None",
                requested_permission="Viewer"
            )
        ],
        status="approved",
        requested_at="2024-01-15T09:00:00Z",
        approved_at="2024-01-15T14:30:00Z",
        approved_by="admin@example.com",
        notes="마케팅 분석용 뷰어 권한"
    ),
    Permission(
        id=2,
        requester_email="manager@example.com",
        requester_name="김매니저",
        client_name="XYZ 기업",
        properties=[
            PropertyPermission(
                property_id="GA_987654321",
                property_name="XYZ 메인 사이트",
                current_permission="Viewer",
                requested_permission="Editor"
            )
        ],
        status="pending",
        requested_at="2024-01-20T10:15:00Z",
        notes="캠페인 관리를 위한 편집 권한 필요"
    ),
    Permission(
        id=3,
        requester_email="analyst@example.com",
        requester_name="박분석가",
        client_name="DEF 스타트업",
        properties=[
            PropertyPermission(
                property_id="GA_456789123",
                property_name="DEF 서비스",
                current_permission="None",
                requested_permission="Viewer"
            ),
            PropertyPermission(
                property_id="GA_456789124",
                property_name="DEF 어드민",
                current_permission="None",
                requested_permission="Editor"
            )
        ],
        status="rejected",
        requested_at="2024-01-18T16:20:00Z",
        notes="권한 부족으로 거부됨"
    ),
    Permission(
        id=4,
        requester_email="developer@example.com",
        requester_name="최개발자",
        client_name="GHI 솔루션",
        properties=[
            PropertyPermission(
                property_id="GA_789123456",
                property_name="GHI 통합 플랫폼",
                current_permission="Editor",
                requested_permission="Administrator"
            )
        ],
        status="pending",
        requested_at="2024-01-19T11:45:00Z",
        notes="통합 개발을 위한 관리자 권한"
    )
]

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보 조회"""
    token = credentials.credentials
    email = verify_token(token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = next((u for u in users_db if u.email == email), None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

app = FastAPI(
    title="GA4 Admin Automation System",
    description="GA4 권한 관리 자동화 시스템",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "GA4 Admin Automation System - Backend is running!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend server is running"}

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """실제 사용자 로그인"""
    # 사용자 찾기
    user = next((u for u in users_db if u.email == email), None)
    
    if not user:
        # 실패한 로그인 시도 기록 (사용자가 존재하지 않는 경우에는 기록하지 않음)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비밀번호 검증
    if not verify_password(password, user.password_hash):
        # 로그인 실패 감사 로그 기록
        create_audit_log(
            action="login",
            user=user,
            target_type="user",
            details="잘못된 비밀번호로 로그인 실패",
            status="failure",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비활성 사용자 체크
    if not user.is_active:
        # 비활성 사용자 로그인 시도 기록
        create_audit_log(
            action="login",
            user=user,
            target_type="user",
            details="비활성화된 계정으로 로그인 시도",
            status="failure",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # 마지막 로그인 시간 업데이트
    user.last_login = datetime.now().isoformat() + "Z"
    
    # 성공한 로그인 감사 로그 기록
    create_audit_log(
        action="login",
        user=user,
        target_type="user",
        details="성공적으로 로그인함",
        status="success",
        request=request
    )
    
    # User 모델로 변환 (password_hash 제외)
    user_response = User(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return User(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

# Permissions API Endpoints
@app.get("/api/permissions", response_model=List[Permission])
@require_permissions(["read_permission"])
async def get_permissions(user: UserInDB = Depends(get_current_user)):
    """권한 목록 조회 - 역할별 접근 제어"""
    # 역할별 권한 필터링
    if user.role in ["Super Admin", "Admin"]:
        # 관리자는 모든 권한 요청 조회 가능
        return permissions_db
    elif user.role == "Requester":
        # Requester는 자신의 권한 요청만 조회 가능
        return [p for p in permissions_db if p.requester_email == user.email]
    else:
        # Viewer는 권한 요청 조회 불가
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot access permission requests"
        )

@app.post("/api/permissions", response_model=Permission)
async def create_permission(
    request: CreatePermissionRequest,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """새 권한 요청 생성 - 역할별 제한사항 적용"""
    # 요청자 정보 조회
    requester_user = next((u for u in users_db if u.email == request.requester_email), None)
    if not requester_user:
        raise HTTPException(status_code=404, detail="Requester not found")
    
    # 자동 승인 여부 확인
    auto_approve = False
    for prop in request.properties:
        required_approver = get_required_approver_role(prop.requested_permission, requester_user.role)
        if required_approver == "auto":
            auto_approve = True
            break
    
    new_id = max([p.id for p in permissions_db], default=0) + 1
    initial_status = "approved" if auto_approve else "pending"
    
    new_permission = Permission(
        id=new_id,
        requester_email=request.requester_email,
        requester_name=requester_user.name,
        client_name=request.client_name,
        properties=request.properties,
        status=initial_status,
        requested_at=datetime.now().isoformat() + "Z",
        notes=request.notes,
        approved_at=datetime.now().isoformat() + "Z" if auto_approve else None,
        approved_by="system_auto_approval" if auto_approve else None
    )
    permissions_db.append(new_permission)
    
    # 감사 로그 기록
    create_audit_log(
        action="create_permission",
        user=user,
        target_type="permission",
        target_id=str(new_id),
        target_name=f"{request.client_name} - {requester_user.name}",
        details=f"권한 요청 생성: {request.requester_email} ({', '.join([f'{p.property_name}:{p.requested_permission}' for p in request.properties])}) - {'자동 승인' if auto_approve else '승인 대기'}",
        request=http_request
    )
    
    # 이메일 알림 발송 (관리자에게)
    try:
        admin_emails = ["admin@example.com", "manager@example.com"]  # 실제로는 DB에서 관리자 이메일 조회
        properties_dict = [
            {
                "property_id": prop.property_id,
                "property_name": prop.property_name,
                "current_permission": prop.current_permission,
                "requested_permission": prop.requested_permission
            }
            for prop in request.properties
        ]
        
        email_service.send_permission_request_notification(
            requester_email=request.requester_email,
            requester_name="새 요청자",
            client_name=request.client_name,
            properties=properties_dict,
            admin_emails=admin_emails
        )
    except Exception as e:
        # 이메일 전송 실패해도 권한 요청은 생성됨
        print(f"이메일 전송 실패: {str(e)}")
    
    return new_permission

@app.put("/api/permissions/{permission_id}")
@require_permissions(["approve_permission", "reject_permission"])
async def update_permission_status(
    permission_id: int,
    request: UpdatePermissionRequest,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """권한 상태 변경 (승인/거부) - 역할별 승인 권한 확인"""
    permission = next((p for p in permissions_db if p.id == permission_id), None)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # 권한 승인 자격 확인
    requester_user = next((u for u in users_db if u.email == permission.requester_email), None)
    if not requester_user:
        raise HTTPException(status_code=404, detail="Permission requester not found")
    
    # 각 속성별 권한 승인 자격 확인
    for prop in permission.properties:
        if not can_approve_permission(user["role"], prop.requested_permission, requester_user.role):
            # 실패 감사 로그 기록
            create_audit_log(
                action="approve_permission" if request.status == "approved" else "reject_permission",
                user=user,
                target_type="permission",
                target_id=str(permission_id),
                target_name=f"{permission.client_name} - {prop.property_name}",
                details=f"권한 {request.status} 실패: {prop.requested_permission} 권한을 승인할 자격 없음",
                status="failure",
                request=http_request
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Cannot approve '{prop.requested_permission}' permission. Required role: {get_required_approver_role(prop.requested_permission, requester_user.role)}"
            )
    
    # 상태 업데이트
    old_status = permission.status
    permission.status = request.status
    
    if request.status == "approved":
        permission.approved_at = datetime.now().isoformat() + "Z"
        permission.approved_by = user["email"]
        
        # 실제 GA4 API를 통한 권한 부여
        try:
            for prop in permission.properties:
                # GA4 역할 매핑
                roles = map_permission_to_ga4_roles(prop.requested_permission)
                
                # 실제 GA4 API 호출
                result = await ga4_client.create_property_access_binding(
                    prop.property_id, 
                    permission.requester_email, 
                    roles
                )
                
                if result:
                    # 성공 시 현재 권한 업데이트
                    prop.current_permission = prop.requested_permission
            
            # 성공 감사 로그 기록
            create_audit_log(
                action="approve_permission",
                user=user,
                target_type="permission",
                target_id=str(permission_id),
                target_name=f"{permission.client_name} - {permission.requester_name}",
                details=f"권한 요청 승인: {permission.requester_email} ({', '.join([f'{p.property_name}:{p.requested_permission}' for p in permission.properties])})",
                request=http_request
            )
            
            # 승인 이메일 발송
            try:
                properties_dict = [
                    {
                        "property_id": prop.property_id,
                        "property_name": prop.property_name,
                        "current_permission": prop.current_permission,
                        "requested_permission": prop.requested_permission
                    }
                    for prop in permission.properties
                ]
                
                email_service.send_permission_approved_notification(
                    requester_email=permission.requester_email,
                    requester_name=permission.requester_name,
                    client_name=permission.client_name,
                    properties=properties_dict,
                    approved_by=user["email"]
                )
            except Exception as e:
                print(f"승인 이메일 전송 실패: {str(e)}")
                    
        except Exception as e:
            # GA4 API 실패 시 상태 롤백
            permission.status = old_status
            permission.approved_at = None
            permission.approved_by = None
            raise HTTPException(
                status_code=500, 
                detail=f"GA4 권한 부여 실패: {str(e)}"
            )
            
    elif request.status == "rejected":
        permission.approved_at = None
        permission.approved_by = None
        
        # 거부 감사 로그 기록
        create_audit_log(
            action="reject_permission",
            user=user,
            target_type="permission",
            target_id=str(permission_id),
            target_name=f"{permission.client_name} - {permission.requester_name}",
            details=f"권한 요청 거부: {permission.requester_email} ({', '.join([f'{p.property_name}:{p.requested_permission}' for p in permission.properties])}) - 사유: {request.notes or '사유 없음'}",
            request=http_request
        )
        
        # 거부 이메일 발송
        try:
            properties_dict = [
                {
                    "property_id": prop.property_id,
                    "property_name": prop.property_name,
                    "current_permission": prop.current_permission,
                    "requested_permission": prop.requested_permission
                }
                for prop in permission.properties
            ]
            
            email_service.send_permission_rejected_notification(
                requester_email=permission.requester_email,
                requester_name=permission.requester_name,
                client_name=permission.client_name,
                properties=properties_dict,
                rejected_by=user["email"],
                reason=request.notes or "추가 정보가 필요합니다."
            )
        except Exception as e:
            print(f"거부 이메일 전송 실패: {str(e)}")
        
    elif request.status == "pending":
        permission.approved_at = None
        permission.approved_by = None
    
    if request.notes:
        permission.notes = request.notes
    
    return {"message": "Permission status updated successfully"}

@app.delete("/api/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    user: dict = Depends(get_current_user)
):
    """권한 요청 삭제"""
    global permissions_db
    permission = next((p for p in permissions_db if p.id == permission_id), None)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    permissions_db = [p for p in permissions_db if p.id != permission_id]
    return {"message": "Permission deleted successfully"}

@app.get("/api/permissions/{permission_id}", response_model=Permission)
async def get_permission_by_id(
    permission_id: int,
    user: dict = Depends(get_current_user)
):
    """특정 권한 요청 조회"""
    permission = next((p for p in permissions_db if p.id == permission_id), None)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission

# GA4 API Endpoints
@app.get("/api/ga4/accounts")
async def get_ga4_accounts(user: dict = Depends(get_current_user)):
    """GA4 계정 목록 조회"""
    try:
        accounts = await ga4_client.get_accounts()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GA4 계정 조회 실패: {str(e)}")

@app.get("/api/ga4/properties")
async def get_ga4_properties(
    account_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """GA4 Property 목록 조회"""
    try:
        properties = await ga4_client.get_properties(account_id)
        return {"properties": properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GA4 Property 조회 실패: {str(e)}")

@app.get("/api/ga4/properties/{property_id}/permissions")
async def get_property_permissions(
    property_id: str,
    user: dict = Depends(get_current_user)
):
    """GA4 Property의 현재 권한 목록 조회"""
    try:
        bindings = await ga4_client.get_property_access_bindings(property_id)
        return {"permissions": bindings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GA4 Property 권한 조회 실패: {str(e)}")

@app.post("/api/ga4/properties/{property_id}/permissions")
async def grant_property_permission(
    property_id: str,
    request: dict,  # {"user_email": "user@example.com", "permission_type": "viewer"}
    user: dict = Depends(get_current_user)
):
    """GA4 Property에 사용자 권한 부여"""
    try:
        user_email = request.get("user_email")
        permission_type = request.get("permission_type")
        
        if not user_email or not permission_type:
            raise HTTPException(status_code=400, detail="user_email and permission_type are required")
        
        # 권한 타입을 GA4 역할로 매핑
        roles = map_permission_to_ga4_roles(permission_type)
        
        # GA4 API를 통한 실제 권한 부여
        result = await ga4_client.create_property_access_binding(property_id, user_email, roles)
        
        if result:
            return {"message": "권한 부여 성공", "binding": result}
        else:
            raise HTTPException(status_code=500, detail="권한 부여 실패")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GA4 Property 권한 부여 실패: {str(e)}")

@app.delete("/api/ga4/properties/{property_id}/permissions/{binding_name}")
async def revoke_property_permission(
    property_id: str,
    binding_name: str,
    user: dict = Depends(get_current_user)
):
    """GA4 Property의 사용자 권한 철회"""
    try:
        success = await ga4_client.delete_property_access_binding(property_id, binding_name)
        
        if success:
            return {"message": "권한 철회 성공"}
        else:
            raise HTTPException(status_code=500, detail="권한 철회 실패")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GA4 Property 권한 철회 실패: {str(e)}")

@app.put("/api/ga4/properties/{property_id}/permissions/{binding_name}")
async def update_property_permission(
    property_id: str,
    binding_name: str,
    request: dict,  # {"permission_type": "editor"}
    user: dict = Depends(get_current_user)
):
    """GA4 Property의 사용자 권한 수정"""
    try:
        permission_type = request.get("permission_type")
        
        if not permission_type:
            raise HTTPException(status_code=400, detail="permission_type is required")
        
        # 권한 타입을 GA4 역할로 매핑
        roles = map_permission_to_ga4_roles(permission_type)
        
        # GA4 API를 통한 실제 권한 수정
        result = await ga4_client.update_property_access_binding(binding_name, roles)
        
        if result:
            return {"message": "권한 수정 성공", "binding": result}
        else:
            raise HTTPException(status_code=500, detail="권한 수정 실패")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GA4 Property 권한 수정 실패: {str(e)}")

# Users API Endpoints
@app.get("/api/users")
@require_permissions(["read_user"])
async def get_users(
    request: Request,
    page: int = 1,
    limit: int = 10,
    user: UserInDB = Depends(get_current_user)
):
    """사용자 목록 조회 - 역할별 권한 적용"""
    try:
        
        # 감사 로그 기록
        create_audit_log(
            action="read_user",
            user=user,
            target_type="user_list",
            details=f"사용자 목록 조회 (page: {page}, limit: {limit})",
            request=request
        )
        
        # 페이지네이션 로직
        start = (page - 1) * limit
        end = start + limit
        
        # 역할별 필터링
        if user.role == "Super Admin":
            # Super Admin은 모든 사용자 조회 가능
            filtered_users = users_db[start:end]
        elif user.role == "Admin":
            # Admin은 Super Admin 제외하고 조회 가능
            all_filtered = [u for u in users_db if u.role != "Super Admin"]
            filtered_users = all_filtered[start:end]
        else:
            # 일반 사용자는 자신만 조회 가능
            all_filtered = [u for u in users_db if u.id == user.id]
            filtered_users = all_filtered[start:end]
        
        # UserInDB를 딕셔너리로 변환
        result = []
        for user_db in filtered_users:
            user_dict = {
                "id": user_db.id,
                "email": user_db.email,
                "name": user_db.name,
                "role": user_db.role,
                "is_active": user_db.is_active,
                "created_at": user_db.created_at,
                "last_login": user_db.last_login
            }
            result.append(user_dict)
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error in get_users: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/users/{user_id}", response_model=User)
@require_permissions(["read_user"])
async def get_user_by_id(
    user_id: int,
    request: Request,
    user: UserInDB = Depends(get_current_user)
):
    """특정 사용자 조회 - 접근 권한 확인"""
    target_user = next((u for u in users_db if u.id == user_id), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 접근 권한 확인
    if not can_access_user(user.role, user.id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own profile"
        )
    
    # 감사 로그 기록
    create_audit_log(
        action="read_user",
        user=user,
        target_type="user",
        target_id=str(user_id),
        target_name=target_user.name,
        details=f"사용자 정보 조회: {target_user.email}",
        request=request
    )
    
    return target_user

@app.post("/api/users", response_model=User)
@require_permissions(["create_user"])
async def create_user(
    request: CreateUserRequest,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """새 사용자 생성 - 역할별 권한 확인"""
    # 역할 생성 권한 확인
    if not can_manage_user_role(user["role"], request.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot create user with role '{request.role}'"
        )
    
    # 이메일 중복 확인
    existing_user = next((u for u in users_db if u.email == request.email), None)
    if existing_user:
        # 실패 감사 로그 기록
        create_audit_log(
            action="create_user",
            user=user,
            target_type="user",
            target_name=request.name,
            details=f"사용자 생성 실패: 이미 존재하는 이메일 ({request.email})",
            status="failure",
            request=http_request
        )
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # 새 사용자 생성
    new_id = max([u.id for u in users_db], default=0) + 1
    new_user_db = UserInDB(
        id=new_id,
        email=request.email,
        name=request.name,
        role=request.role,
        is_active=True,
        created_at=datetime.now().isoformat() + "Z",
        password_hash=hash_password("defaultpassword123")  # 기본 비밀번호 설정
    )
    users_db.append(new_user_db)
    
    # 성공 감사 로그 기록
    create_audit_log(
        action="create_user",
        user=user,
        target_type="user",
        target_id=str(new_id),
        target_name=request.name,
        details=f"새 사용자 생성: {request.email} (역할: {request.role})",
        request=http_request
    )
    
    # 응답용 User 객체 반환
    return User(
        id=new_user_db.id,
        email=new_user_db.email,
        name=new_user_db.name,
        role=new_user_db.role,
        is_active=new_user_db.is_active,
        created_at=new_user_db.created_at,
        last_login=new_user_db.last_login
    )

@app.put("/api/users/{user_id}", response_model=User)
@require_permissions(["update_user"])
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """사용자 정보 수정 - 역할별 권한 확인"""
    target_user = next((u for u in users_db if u.id == user_id), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 자기 자신 수정인지 확인
    is_self_update = (user["id"] == user_id)
    
    # 권한 확인: 자기 자신이거나 관리 권한이 있어야 함
    if not is_self_update:
        if not can_access_user(user["role"], user["id"], user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only edit your own profile"
            )
        
        # 역할 변경 권한 확인
        if request.role and not can_manage_user_role(user["role"], target_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Cannot modify user with role '{target_user.role}'"
            )
        
        if request.role and not can_manage_user_role(user["role"], request.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Cannot assign role '{request.role}'"
            )
    else:
        # 자기 자신 수정 시 제한사항
        if request.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot change your own role"
            )
        if request.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot change your own active status"
            )
    
    # 이메일 중복 확인 (다른 사용자와)
    if request.email and request.email != target_user.email:
        existing_user = next((u for u in users_db if u.email == request.email), None)
        if existing_user:
            # 실패 감사 로그 기록
            create_audit_log(
                action="update_user",
                user=user,
                target_type="user",
                target_id=str(user_id),
                target_name=target_user.name,
                details=f"사용자 수정 실패: 이미 존재하는 이메일 ({request.email})",
                status="failure",
                request=http_request
            )
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # 변경사항 추적을 위한 이전 값 저장
    old_values = {
        "email": target_user.email,
        "name": target_user.name,
        "role": target_user.role,
        "is_active": target_user.is_active
    }
    
    # 업데이트 적용
    changes = []
    if request.email is not None and request.email != target_user.email:
        target_user.email = request.email
        changes.append(f"이메일: {old_values['email']} → {request.email}")
    if request.name is not None and request.name != target_user.name:
        target_user.name = request.name
        changes.append(f"이름: {old_values['name']} → {request.name}")
    if request.role is not None and request.role != target_user.role:
        target_user.role = request.role
        changes.append(f"역할: {old_values['role']} → {request.role}")
    if request.is_active is not None and request.is_active != target_user.is_active:
        target_user.is_active = request.is_active
        changes.append(f"활성상태: {old_values['is_active']} → {request.is_active}")
    
    # 감사 로그 기록
    if changes:
        create_audit_log(
            action="update_user",
            user=user,
            target_type="user",
            target_id=str(user_id),
            target_name=target_user.name,
            details=f"사용자 정보 수정: {', '.join(changes)}",
            request=http_request
        )
    
    # 응답용 User 객체 반환
    return User(
        id=target_user.id,
        email=target_user.email,
        name=target_user.name,
        role=target_user.role,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        last_login=target_user.last_login
    )

@app.delete("/api/users/{user_id}")
@require_permissions(["delete_user"])
async def delete_user(
    user_id: int,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """사용자 삭제 - 역할별 권한 확인"""
    global users_db
    target_user = next((u for u in users_db if u.id == user_id), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 자기 자신은 삭제할 수 없음
    if target_user.id == user["id"]:
        # 실패 감사 로그 기록
        create_audit_log(
            action="delete_user",
            user=user,
            target_type="user",
            target_id=str(user_id),
            target_name=target_user.name,
            details="사용자 삭제 실패: 자기 자신을 삭제할 수 없음",
            status="failure",
            request=http_request
        )
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # 역할 관리 권한 확인
    if not can_manage_user_role(user["role"], target_user.role):
        # 실패 감사 로그 기록
        create_audit_log(
            action="delete_user",
            user=user,
            target_type="user",
            target_id=str(user_id),
            target_name=target_user.name,
            details=f"사용자 삭제 실패: {target_user.role} 역할을 가진 사용자를 삭제할 권한 없음",
            status="failure",
            request=http_request
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot delete user with role '{target_user.role}'"
        )
    
    # 사용자 삭제
    users_db = [u for u in users_db if u.id != user_id]
    
    # 성공 감사 로그 기록
    create_audit_log(
        action="delete_user",
        user=user,
        target_type="user",
        target_id=str(user_id),
        target_name=target_user.name,
        details=f"사용자 삭제: {target_user.email} (역할: {target_user.role})",
        request=http_request
    )
    
    return {"message": "User deleted successfully"}

# Clients API Endpoints
@app.get("/api/clients", response_model=List[Client])
@require_permissions(["read_client"])
async def get_clients(
    page: int = 1,
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """클라이언트 목록 조회 - 역할별 접근 제어 적용"""
    # 사용자가 접근 가능한 클라이언트 필터링
    accessible_client_ids = get_user_accessible_clients(user["id"], user["role"])
    filtered_clients = [c for c in clients_db if c.id in accessible_client_ids]
    
    # 페이지네이션 로직
    start = (page - 1) * limit
    end = start + limit
    
    paginated_clients = filtered_clients[start:end]
    return paginated_clients

@app.get("/api/clients/{client_id}", response_model=Client)
async def get_client_by_id(
    client_id: int,
    user: dict = Depends(get_current_user)
):
    """특정 클라이언트 조회"""
    client = next((c for c in clients_db if c.id == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.post("/api/clients", response_model=Client)
async def create_client(
    request: CreateClientRequest,
    user: dict = Depends(get_current_user)
):
    """새 클라이언트 생성"""
    # 이메일 중복 확인
    existing_client = next((c for c in clients_db if c.contact_email == request.contact_email), None)
    if existing_client:
        raise HTTPException(status_code=400, detail="Contact email already exists")
    
    # GA4 Property ID 중복 확인
    existing_property = next((c for c in clients_db if c.ga4_property_id == request.ga4_property_id), None)
    if existing_property:
        raise HTTPException(status_code=400, detail="GA4 Property ID already exists")
    
    new_id = max([c.id for c in clients_db], default=0) + 1
    current_time = datetime.now().isoformat() + "Z"
    new_client = Client(
        id=new_id,
        name=request.name,
        company_name=request.company_name,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone,
        ga4_property_id=request.ga4_property_id,
        is_active=True,
        created_at=current_time,
        last_updated=current_time,
        user_count=0,
        description=request.description
    )
    clients_db.append(new_client)
    return new_client

@app.put("/api/clients/{client_id}", response_model=Client)
async def update_client(
    client_id: int,
    request: UpdateClientRequest,
    user: dict = Depends(get_current_user)
):
    """클라이언트 정보 수정"""
    client = next((c for c in clients_db if c.id == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 이메일 중복 확인 (다른 클라이언트와)
    if request.contact_email and request.contact_email != client.contact_email:
        existing_client = next((c for c in clients_db if c.contact_email == request.contact_email), None)
        if existing_client:
            raise HTTPException(status_code=400, detail="Contact email already exists")
    
    # GA4 Property ID 중복 확인 (다른 클라이언트와)
    if request.ga4_property_id and request.ga4_property_id != client.ga4_property_id:
        existing_property = next((c for c in clients_db if c.ga4_property_id == request.ga4_property_id), None)
        if existing_property:
            raise HTTPException(status_code=400, detail="GA4 Property ID already exists")
    
    # 업데이트 적용
    if request.name is not None:
        client.name = request.name
    if request.company_name is not None:
        client.company_name = request.company_name
    if request.contact_email is not None:
        client.contact_email = request.contact_email
    if request.contact_phone is not None:
        client.contact_phone = request.contact_phone
    if request.ga4_property_id is not None:
        client.ga4_property_id = request.ga4_property_id
    if request.is_active is not None:
        client.is_active = request.is_active
    if request.description is not None:
        client.description = request.description
    
    client.last_updated = datetime.now().isoformat() + "Z"
    return client

@app.delete("/api/clients/{client_id}")
@require_permissions(["delete_client"])
async def delete_client(
    client_id: int,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """클라이언트 삭제 - 관련 할당 삭제 포함"""
    global clients_db, client_assignments_db
    client = next((c for c in clients_db if c.id == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 클라이언트와 관련된 할당 삭제
    related_assignments = [a for a in client_assignments_db if a.client_id == client_id]
    assignment_count = len(related_assignments)
    
    client_assignments_db = [a for a in client_assignments_db if a.client_id != client_id]
    clients_db = [c for c in clients_db if c.id != client_id]
    
    # 감사 로그 기록
    create_audit_log(
        action="delete_client",
        user=user,
        target_type="client",
        target_id=str(client_id),
        target_name=client.name,
        details=f"클라이언트 삭제: {client.name} (관련 할당 {assignment_count}개 삭제)",
        request=http_request
    )
    
    return {"message": "Client deleted successfully", "deleted_assignments": assignment_count}

# Audit Logs API Endpoints
@app.get("/api/audit-logs", response_model=List[AuditLog])
@require_permissions(["read_audit_log"])
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action: Optional[str] = None,
    user_email: Optional[str] = None,
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """감사 로그 목록 조회 - 역할별 접근 제어"""
    # 역할별 접근 제어
    filtered_logs = audit_logs_db
    
    if user["role"] == "Super Admin":
        # Super Admin은 모든 로그 조회 가능 (제한 없음)
        pass
    elif user["role"] == "Admin":
        # Admin은 Super Admin의 행동 로그는 제외
        filtered_logs = [log for log in filtered_logs if log.user_email != "admin@example.com"]
    else:
        # Requester/Viewer는 자신의 로그만 조회 가능
        filtered_logs = [log for log in filtered_logs if log.user_email == user["email"]]
    
    if action:
        filtered_logs = [log for log in filtered_logs if action.lower() in log.action.lower()]
    
    if user_email:
        filtered_logs = [log for log in filtered_logs if user_email.lower() in log.user_email.lower()]
    
    if target_type:
        filtered_logs = [log for log in filtered_logs if log.target_type == target_type]
    
    if status:
        filtered_logs = [log for log in filtered_logs if log.status == status]
    
    # 최신순 정렬
    filtered_logs = sorted(filtered_logs, key=lambda x: x.timestamp, reverse=True)
    
    # 페이지네이션 적용
    start = (page - 1) * limit
    end = start + limit
    
    paginated_logs = filtered_logs[start:end]
    return paginated_logs

@app.get("/api/audit-logs/stats")
@require_permissions(["read_audit_log"])
async def get_audit_log_stats(user: dict = Depends(get_current_user)):
    """감사 로그 통계 조회"""
    total_logs = len(audit_logs_db)
    success_logs = len([log for log in audit_logs_db if log.status == "success"])
    failure_logs = len([log for log in audit_logs_db if log.status == "failure"])
    warning_logs = len([log for log in audit_logs_db if log.status == "warning"])
    
    # 액션 타입별 통계
    action_stats = {}
    for log in audit_logs_db:
        action_stats[log.action] = action_stats.get(log.action, 0) + 1
    
    # 타겟 타입별 통계
    target_stats = {}
    for log in audit_logs_db:
        target_stats[log.target_type] = target_stats.get(log.target_type, 0) + 1
    
    return {
        "total_logs": total_logs,
        "success_logs": success_logs,
        "failure_logs": failure_logs,
        "warning_logs": warning_logs,
        "action_stats": action_stats,
        "target_stats": target_stats
    }

@app.get("/api/audit-logs/{log_id}", response_model=AuditLog)
async def get_audit_log_by_id(
    log_id: int,
    user: dict = Depends(get_current_user)
):
    """특정 감사 로그 조회"""
    log = next((l for l in audit_logs_db if l.id == log_id), None)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log

# Client Assignment API Endpoints
@app.post("/api/client-assignments", response_model=ClientAssignment, status_code=status.HTTP_201_CREATED)
@require_permissions(["manage_client_assignments"])
async def create_client_assignment(
    request: CreateClientAssignmentRequest,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """새 클라이언트 할당 생성"""
    # 사용자와 클라이언트 존재 확인
    target_user = next((u for u in users_db if u.id == request.user_id), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_client = next((c for c in clients_db if c.id == request.client_id), None)
    if not target_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 기존 할당 확인
    existing_assignment = next(
        (a for a in client_assignments_db 
         if a.user_id == request.user_id and a.client_id == request.client_id),
        None
    )
    if existing_assignment:
        raise HTTPException(status_code=400, detail="User is already assigned to this client")
    
    # 새 할당 생성
    new_id = max([a.id for a in client_assignments_db], default=0) + 1
    current_time = datetime.now().isoformat() + "Z"
    
    new_assignment = ClientAssignment(
        id=new_id,
        user_id=request.user_id,
        client_id=request.client_id,
        assigned_by_id=user["id"],
        status=request.status,
        assigned_at=current_time,
        expires_at=request.expires_at,
        notes=request.notes,
        created_at=current_time,
        updated_at=current_time
    )
    
    client_assignments_db.append(new_assignment)
    
    # 감사 로그 기록
    create_audit_log(
        action="create_client_assignment",
        user=user,
        target_type="client_assignment",
        target_id=str(new_id),
        target_name=f"{target_user.name} -> {target_client.name}",
        details=f"클라이언트 할당 생성: {target_user.email} → {target_client.name} (상태: {request.status})",
        request=http_request
    )
    
    return new_assignment

@app.get("/api/client-assignments", response_model=List[ClientAssignment])
async def get_client_assignments(
    user_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    include_inactive: bool = False,
    user: UserInDB = Depends(get_current_user)
):
    """클라이언트 할당 목록 조회 - 역할별 필터링"""
    assignments = client_assignments_db
    
    # 역할별 필터링
    if user.role == "Super Admin":
        # Super Admin은 모든 할당 조회 가능
        pass
    elif user.role == "Admin":
        # Admin은 접근 가능한 클라이언트의 할당만 조회 가능
        accessible_clients = get_user_accessible_clients(user.id, user.role)
        if client_id and client_id not in accessible_clients:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to client assignments"
            )
        assignments = [a for a in assignments if a.client_id in accessible_clients]
    else:
        # 일반 사용자는 자신의 할당만 조회 가능
        assignments = [a for a in assignments if a.user_id == user.id]
    
    # 필터 적용
    if user_id:
        assignments = [a for a in assignments if a.user_id == user_id]
    if client_id:
        assignments = [a for a in assignments if a.client_id == client_id]
    if status:
        assignments = [a for a in assignments if a.status == status]
    if not include_inactive:
        assignments = [a for a in assignments if a.status == "active"]
    
    return assignments

@app.delete("/api/client-assignments/{assignment_id}")
@require_permissions(["manage_client_assignments"])
async def delete_client_assignment(
    assignment_id: int,
    http_request: Request,
    user: dict = Depends(get_current_user)
):
    """클라이언트 할당 삭제"""
    global client_assignments_db
    assignment = next((a for a in client_assignments_db if a.id == assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Client assignment not found")
    
    # 사용자와 클라이언트 정보 가져오기
    target_user = next((u for u in users_db if u.id == assignment.user_id), None)
    target_client = next((c for c in clients_db if c.id == assignment.client_id), None)
    
    client_assignments_db = [a for a in client_assignments_db if a.id != assignment_id]
    
    # 감사 로그 기록
    create_audit_log(
        action="delete_client_assignment",
        user=user,
        target_type="client_assignment",
        target_id=str(assignment_id),
        target_name=f"{target_user.name if target_user else 'Unknown'} -> {target_client.name if target_client else 'Unknown'}",
        details=f"할당 삭제: {target_user.email if target_user else 'Unknown'} 에서 {target_client.name if target_client else 'Unknown'} 할당 제거",
        request=http_request
    )
    
    return {"message": "Client assignment deleted successfully"}

@app.get("/api/my/accessible-clients")
async def get_my_accessible_clients(
    user: UserInDB = Depends(get_current_user)
):
    """현재 사용자가 접근 가능한 클라이언트 목록 조회"""
    try:
        accessible_client_ids = get_user_accessible_clients(user.id, user.role)
        return {"accessible_client_ids": accessible_client_ids}
    except Exception as e:
        print(f"Error in get_my_accessible_clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate-client-access/{client_id}")
async def validate_client_access(
    client_id: int,
    user: UserInDB = Depends(get_current_user)
):
    """현재 사용자의 클라이언트 접근 권한 확인"""
    has_access = check_user_client_access(user.id, client_id, user.role)
    
    return {
        "user_id": user.id,
        "client_id": client_id,
        "has_access": has_access,
        "role": user.role
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting GA4 Admin Backend Server...")
    print("📋 테스트 계정 정보:")
    print("=" * 50)
    print("🔑 관리자 계정:")
    print("   이메일: admin@example.com")
    print("   비밀번호: admin123")
    print("   역할: Super Admin")
    print()
    print("👤 일반 사용자 계정:")
    print("   이메일: user@example.com")
    print("   비밀번호: user123") 
    print("   역할: Requester")
    print("=" * 50)
    print("🌐 Backend URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)