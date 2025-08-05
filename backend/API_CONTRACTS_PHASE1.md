# GA4 Admin Automation System - API Contracts Phase 1

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: TBD

## Authentication Flow

### 1. User Registration
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe",
  "company": "Example Corp"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "Requester",
  "status": "inactive",
  "registration_status": "pending_verification",
  "created_at": "2025-08-05T14:20:14"
}
```

### 2. User Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "Requester"
  }
}
```

### 3. Token Refresh
```http
POST /api/auth/refresh
Authorization: Bearer {refresh_token}
```

### 4. Get Current User
```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

## User Management

### 1. List Users (Admin/Super Admin only)
```http
GET /api/users/?limit=10&offset=0&role=REQUESTER
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "Requester",
      "status": "active",
      "created_at": "2025-08-05T14:20:14"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

### 2. Update User
```http
PUT /api/users/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Name",
  "role": "ADMIN"
}
```

## Health Checks

### 1. Basic Health Check
```http
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": 1754403596.512064,
  "service": "ga4-admin-backend",
  "version": "2.0.0"
}
```

### 2. Detailed Health Check
```http
GET /health/detailed
```

## Error Responses

### Authentication Errors
```json
{
  "detail": "Invalid email or password"
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "input": "invalid-email"
    }
  ]
}
```

### Authorization Errors
```json
{
  "error": "INSUFFICIENT_PERMISSIONS",
  "message": "Insufficient permissions to access this resource",
  "details": {
    "required_role": "ADMIN",
    "user_role": "REQUESTER"
  }
}
```

## User Roles & Permissions

### Available Roles:
- **SUPER_ADMIN** - Full system access
- **ADMIN** - User and client management
- **REQUESTER** - Request permissions, view own data
- **VIEWER** - Read-only access to assigned data

### Status Values:
- **active** - User can login and use system
- **inactive** - User account disabled
- **pending_verification** - New account awaiting email verification

## Rate Limiting
- **Authentication**: 5 requests per minute per IP
- **API calls**: 100 requests per minute per user
- **Registration**: 3 requests per hour per IP

## CORS Configuration
- **Allowed Origins**: Frontend domains
- **Allowed Methods**: GET, POST, PUT, DELETE, PATCH
- **Allowed Headers**: Authorization, Content-Type
- **Credentials**: Supported

## WebSocket Support
- Real-time notifications available at `/ws/notifications`
- Requires valid JWT token for connection

## File Upload Endpoints
- Profile pictures: `POST /api/users/{user_id}/avatar`
- Document uploads: `POST /api/documents/`
- Max file size: 10MB

## Advanced Features Available (Phase 2+)
- GA4 property management
- Permission request workflows
- Client assignment system
- Service account management
- Audit logging
- AI analytics insights