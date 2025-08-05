# GA4 Admin Automation System - Backend Specification

## Overview

The backend of the GA4 Admin Automation System is built with FastAPI, providing a high-performance, async REST API with comprehensive security, scalability, and integration capabilities. This specification details the complete backend architecture, API design, and implementation strategy.

## Architecture

### Tech Stack
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0 with async support
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Authentication**: JWT with refresh tokens
- **Task Queue**: Celery with Redis broker
- **API Documentation**: OpenAPI 3.0 (Swagger)
- **Testing**: Pytest with async support

### Directory Structure
```
backend/
├── src/
│   ├── api/
│   │   ├── routers/          # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── permissions.py
│   │   │   ├── clients.py
│   │   │   ├── ga4.py
│   │   │   ├── notifications.py
│   │   │   ├── audit.py
│   │   │   └── health.py
│   │   ├── dependencies/     # Dependency injection
│   │   ├── middleware/       # Custom middleware
│   │   └── websockets/       # WebSocket handlers
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connection
│   │   ├── security.py      # Auth utilities
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── logging.py       # Logging config
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── repositories/        # Data access layer
│   ├── tasks/              # Celery tasks
│   ├── utils/              # Utilities
│   └── main.py             # FastAPI app
├── migrations/             # Alembic migrations
├── tests/                  # Test files
├── scripts/                # Utility scripts
└── requirements.txt
```

## Database Design

### Core Models

#### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    email: str = Column(String(255), unique=True, nullable=False)
    password_hash: str = Column(String(255), nullable=False)
    full_name: str = Column(String(255), nullable=False)
    role: UserRole = Column(Enum(UserRole), nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=utc_now)
    updated_at: datetime = Column(DateTime, onupdate=utc_now)
    
    # Relationships
    client_id: UUID = Column(UUID, ForeignKey("clients.id"))
    permissions = relationship("Permission", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
```

#### Permission Model
```python
class Permission(Base):
    __tablename__ = "permissions"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID, ForeignKey("users.id"))
    ga4_property_id: str = Column(String(255), nullable=False)
    ga4_account_id: str = Column(String(255), nullable=False)
    permission_type: PermissionType = Column(Enum(PermissionType))
    status: PermissionStatus = Column(Enum(PermissionStatus))
    requested_at: datetime = Column(DateTime, default=utc_now)
    approved_at: datetime = Column(DateTime, nullable=True)
    expires_at: datetime = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="permissions")
    approver_id: UUID = Column(UUID, ForeignKey("users.id"))
```

#### Client Model
```python
class Client(Base):
    __tablename__ = "clients"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    name: str = Column(String(255), nullable=False)
    domain: str = Column(String(255), unique=True)
    is_active: bool = Column(Boolean, default=True)
    settings: dict = Column(JSON, default=dict)
    
    # Relationships
    users = relationship("User", back_populates="client")
    service_accounts = relationship("ServiceAccount", back_populates="client")
```

#### ServiceAccount Model
```python
class ServiceAccount(Base):
    __tablename__ = "service_accounts"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    client_id: UUID = Column(UUID, ForeignKey("clients.id"))
    email: str = Column(String(255), unique=True)
    key_data: dict = Column(JSON)  # Encrypted
    is_active: bool = Column(Boolean, default=True)
    
    # Relationships
    client = relationship("Client", back_populates="service_accounts")
```

#### AuditLog Model
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID, ForeignKey("users.id"))
    action: str = Column(String(100), nullable=False)
    resource_type: str = Column(String(50))
    resource_id: str = Column(String(255))
    details: dict = Column(JSON, default=dict)
    ip_address: str = Column(String(45))
    user_agent: str = Column(String(500))
    timestamp: datetime = Column(DateTime, default=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
```

## API Design

### Authentication Endpoints

#### POST /api/auth/register
```python
@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register a new user
    - Validate email uniqueness
    - Hash password
    - Create user record
    - Send verification email
    - Return user data
    """
```

#### POST /api/auth/login
```python
@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginCredentials,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    User login
    - Validate credentials
    - Generate JWT tokens
    - Create audit log
    - Return tokens
    """
```

#### POST /api/auth/refresh
```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token
    - Validate refresh token
    - Generate new access token
    - Optionally rotate refresh token
    - Return new tokens
    """
```

### User Management Endpoints

#### GET /api/users
```python
@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    client_id: UUID = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[UserResponse]:
    """
    List users with pagination and filters
    - Check permissions
    - Apply filters
    - Return paginated results
    """
```

#### PUT /api/users/{user_id}
```python
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update user details
    - Validate permissions
    - Update user record
    - Create audit log
    - Return updated user
    """
```

### Permission Management Endpoints

#### POST /api/permissions
```python
@router.post("/", response_model=PermissionResponse)
async def request_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PermissionResponse:
    """
    Request new permission
    - Validate GA4 property access
    - Create permission request
    - Send notification to approvers
    - Return permission details
    """
```

#### POST /api/permissions/{permission_id}/approve
```python
@router.post("/{permission_id}/approve", response_model=PermissionResponse)
async def approve_permission(
    permission_id: UUID,
    approval_data: PermissionApproval,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PermissionResponse:
    """
    Approve permission request
    - Validate approver permissions
    - Grant GA4 access
    - Update permission status
    - Send notification to requester
    - Create audit log
    """
```

### GA4 Integration Endpoints

#### GET /api/ga4/accounts
```python
@router.get("/accounts", response_model=List[GA4AccountResponse])
async def list_ga4_accounts(
    service_account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[GA4AccountResponse]:
    """
    List GA4 accounts
    - Validate service account access
    - Fetch accounts from GA4 API
    - Cache results
    - Return account list
    """
```

#### POST /api/ga4/properties/{property_id}/grant-access
```python
@router.post("/properties/{property_id}/grant-access")
async def grant_property_access(
    property_id: str,
    grant_data: PropertyAccessGrant,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Grant GA4 property access
    - Validate permissions
    - Call GA4 API to grant access
    - Handle rate limiting
    - Create audit log
    - Return success status
    """
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
**Time Estimate**: 40 hours
**Agent**: Backend Agent 5 & 6

#### Tasks:
1. **Project Setup** (Day 1)
   - Initialize FastAPI project
   - Setup project structure
   - Configure dependencies
   - Setup Docker environment
   - **Git Commit**: Every 30 minutes

2. **Database Setup** (Day 2)
   - Design database schema
   - Setup SQLAlchemy models
   - Configure Alembic migrations
   - Create initial migrations
   - **Git Commit**: Every 30 minutes

3. **Authentication System** (Day 3-4)
   - JWT implementation
   - Password hashing
   - Token refresh mechanism
   - Auth middleware
   - **Git Commit**: Every 30 minutes

4. **Base API Structure** (Day 5)
   - Router setup
   - Dependency injection
   - Error handling
   - Logging configuration
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ API server starts successfully
- ✓ Database migrations work
- ✓ Authentication functional
- ✓ API documentation generated

**QA Checkpoints**:
- [ ] All endpoints return proper status codes
- [ ] Database connections stable
- [ ] JWT tokens validate correctly
- [ ] Error responses consistent

### Phase 2: Core Features (Week 2)
**Time Estimate**: 40 hours
**Agent**: Backend Agent 5 & 7

#### Tasks:
1. **User Management API** (Day 6-7)
   - User CRUD endpoints
   - Role-based permissions
   - User search/filter
   - Pagination support
   - **Git Commit**: Every 30 minutes

2. **Permission Management API** (Day 8-9)
   - Permission request endpoints
   - Approval workflow
   - Status tracking
   - Expiration handling
   - **Git Commit**: Every 30 minutes

3. **Client Management API** (Day 10)
   - Client CRUD endpoints
   - Multi-tenant support
   - Settings management
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ All CRUD operations work
- ✓ Permissions enforced
- ✓ Multi-tenant isolation
- ✓ Data validation complete

**QA Checkpoints**:
- [ ] Authorization checks pass
- [ ] Data isolation verified
- [ ] Input validation working
- [ ] Error handling consistent

### Phase 3: GA4 Integration (Week 3)
**Time Estimate**: 40 hours
**Agent**: Backend Agent 7 & 8

#### Tasks:
1. **GA4 API Client** (Day 11-12)
   - Google API setup
   - OAuth2 implementation
   - API wrapper classes
   - Error handling
   - **Git Commit**: Every 30 minutes

2. **Service Account Management** (Day 13)
   - Service account CRUD
   - Credential encryption
   - Validation endpoints
   - **Git Commit**: Every 30 minutes

3. **GA4 Operations** (Day 14-15)
   - Property listing
   - User access management
   - Permission sync
   - Rate limiting
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ GA4 API calls successful
- ✓ Service accounts secure
- ✓ Rate limiting works
- ✓ Data sync accurate

**QA Checkpoints**:
- [ ] API authentication works
- [ ] Credentials encrypted properly
- [ ] Rate limits enforced
- [ ] Error recovery functional

### Phase 4: Advanced Features (Week 4)
**Time Estimate**: 40 hours
**Agent**: Backend Agent 6 & 8

#### Tasks:
1. **Notification System** (Day 16-17)
   - Email service setup
   - Template engine
   - Queue implementation
   - Delivery tracking
   - **Git Commit**: Every 30 minutes

2. **Audit Logging** (Day 18)
   - Audit log service
   - Activity tracking
   - Query endpoints
   - Export functionality
   - **Git Commit**: Every 30 minutes

3. **Background Tasks** (Day 19)
   - Celery setup
   - Scheduled tasks
   - Permission expiration
   - Report generation
   - **Git Commit**: Every 30 minutes

4. **WebSocket Support** (Day 20)
   - WebSocket handlers
   - Real-time notifications
   - Connection management
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ Emails sending reliably
- ✓ Audit logs comprehensive
- ✓ Background tasks running
- ✓ Real-time updates working

**QA Checkpoints**:
- [ ] Email delivery verified
- [ ] Audit logs accurate
- [ ] Tasks execute on schedule
- [ ] WebSocket connections stable

### Phase 5: Optimization & Security (Week 5)
**Time Estimate**: 40 hours
**Agent**: Backend Agent 5-8 (collaborative)

#### Tasks:
1. **Performance Optimization** (Day 21-22)
   - Query optimization
   - Caching implementation
   - Connection pooling
   - Load testing
   - **Git Commit**: Every 30 minutes

2. **Security Hardening** (Day 23)
   - Security audit
   - Input sanitization
   - Rate limiting
   - CORS configuration
   - **Git Commit**: Every 30 minutes

3. **Testing** (Day 24)
   - Unit tests
   - Integration tests
   - API tests
   - Performance tests
   - **Git Commit**: Every 30 minutes

4. **Documentation** (Day 25)
   - API documentation
   - Code documentation
   - Deployment guide
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ Performance targets met
- ✓ Security audit passed
- ✓ Test coverage >80%
- ✓ Documentation complete

**QA Checkpoints**:
- [ ] Load tests pass
- [ ] Security scan clean
- [ ] All tests passing
- [ ] Docs accurate

## Service Layer Architecture

### Repository Pattern
```python
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> User:
        """Get user by ID"""
    
    async def get_by_email(self, email: str) -> User:
        """Get user by email"""
    
    async def create(self, user_data: dict) -> User:
        """Create new user"""
    
    async def update(self, user_id: UUID, data: dict) -> User:
        """Update user"""
```

### Service Layer
```python
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    async def register_user(self, user_data: UserCreate) -> User:
        """
        Business logic for user registration
        - Validate data
        - Hash password
        - Create user
        - Send welcome email
        """
    
    async def update_user_role(
        self, user_id: UUID, 
        new_role: UserRole,
        admin: User
    ) -> User:
        """
        Business logic for role updates
        - Validate permissions
        - Update role
        - Create audit log
        - Send notification
        """
```

## Security Implementation

### JWT Configuration
```python
class JWTSettings:
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

### Permission Decorators
```python
def require_role(allowed_roles: List[UserRole]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Rate Limiting
```python
class RateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.cache = Redis()
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if rate limit exceeded"""
```

## Error Handling

### Custom Exceptions
```python
class AppException(Exception):
    """Base application exception"""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An error occurred"

class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    
class ValidationError(AppException):
    status_code = 400
    error_code = "VALIDATION_ERROR"
    
class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
```

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "request_id": "uuid-here",
  "timestamp": "2024-01-20T10:00:00Z"
}
```

## Background Tasks

### Celery Tasks
```python
@celery_app.task
def send_email_notification(
    to_email: str,
    template: str,
    context: dict
):
    """Send email notification"""

@celery_app.task
def expire_permissions():
    """Check and expire permissions"""

@celery_app.task
def generate_analytics_report(
    client_id: UUID,
    date_range: dict
):
    """Generate analytics report"""
```

### Scheduled Tasks
```python
celery_beat_schedule = {
    'expire-permissions': {
        'task': 'expire_permissions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'daily-summary': {
        'task': 'send_daily_summary',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
}
```

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test user creation"""
    service = UserService(UserRepository(db_session))
    user_data = UserCreate(
        email="test@example.com",
        password="secure_password",
        full_name="Test User"
    )
    user = await service.register_user(user_data)
    assert user.email == user_data.email
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_login_flow(client, db_session):
    """Test complete login flow"""
    # Register user
    # Login
    # Validate tokens
    # Access protected endpoint
```

### API Tests
```python
def test_api_endpoints(test_client):
    """Test API endpoints"""
    response = test_client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Common Error Patterns & Solutions

### 1. Database Connection Issues
**Problem**: Connection pool exhaustion
**Solution**: Implement connection pooling with proper limits

### 2. JWT Token Expiration
**Problem**: Tokens expire during long operations
**Solution**: Implement token refresh middleware

### 3. GA4 API Rate Limits
**Problem**: 429 errors from Google API
**Solution**: Implement exponential backoff and request queuing

### 4. Async Context Issues
**Problem**: Context lost in async operations
**Solution**: Use contextvars for request context

## Agent Responsibilities

### Backend Agent 5 - API Development
- FastAPI route implementation
- Request/response handling
- Middleware development
- API documentation

### Backend Agent 6 - Database & Models
- SQLAlchemy model design
- Migration management
- Query optimization
- Data access layer

### Backend Agent 7 - GA4 Integration
- Google API client
- OAuth2 implementation
- Rate limiting
- Data synchronization

### Backend Agent 8 - Security & Auth
- JWT implementation
- Permission system
- Security hardening
- Audit logging

## Performance Considerations

### Optimization Strategies
1. **Database**
   - Connection pooling
   - Query optimization
   - Proper indexing
   - Read replicas

2. **Caching**
   - Redis for sessions
   - API response caching
   - Query result caching
   - CDN for static assets

3. **Async Operations**
   - Async database queries
   - Background task queues
   - Non-blocking I/O
   - Connection pooling

### Performance Targets
- API response time: <200ms (p95)
- Database query time: <100ms
- Background task processing: <5s
- Concurrent users: 1000+

## Monitoring & Logging

### Logging Configuration
```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "app.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    }
}
```

### Metrics Collection
- Request count and latency
- Error rates by endpoint
- Database query performance
- External API call metrics
- Background task execution

---

**Document Version**: 1.0.0  
**Last Updated**: 2024-01-20  
**Dependencies**: main-spec.md, database design