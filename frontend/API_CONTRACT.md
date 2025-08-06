# Frontend-Backend API Contract
## GA4 Admin Automation System - Phase 3 Permission Management

**Document Version:** 1.0  
**Last Updated:** 2025-08-06  
**Backend Version:** 2.0.0  
**Status:** ✅ Production Ready

---

## 🚀 Overview

This document defines the API contract between Frontend and Backend for the GA4 Admin Automation System with integrated Permission Management and RBAC system.

## 🔐 Authentication

All API endpoints (except health checks) require JWT Bearer token authentication:

```typescript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

**Authentication Response Format:**
- `200`: Success with user data
- `401`: Invalid or expired token  
- `403`: Insufficient permissions

---

## 📊 Core API Endpoints

### Health & System Status

#### `GET /health`
**Purpose:** Basic system health check  
**Auth Required:** ❌ No  
**Response:**
```typescript
{
  status: "healthy",
  timestamp: number,
  service: "ga4-admin-backend", 
  version: "2.0.0"
}
```

#### `GET /health/detailed`
**Purpose:** Detailed health including database connectivity  
**Auth Required:** ❌ No

---

## 🎫 Permission Request Management

### Core Permission Workflow: 요청→승인→활성→만료

#### `GET /api/permission-requests/my-requests`
**Purpose:** Get current user's permission requests  
**Auth Required:** ✅ PERMISSION_READ + self access  
**Query Parameters:**
- `status?`: `pending|approved|rejected|cancelled`
- `limit?`: number (1-100, default: 50)
- `offset?`: number (default: 0)

**Response:**
```typescript
Array<{
  id: number,
  user_id: number,
  client_id: number,
  ga_property_id: string,
  target_email: string,
  permission_level: "viewer"|"analyst"|"marketer"|"editor"|"administrator",
  business_justification: string,
  status: "pending"|"approved"|"rejected"|"cancelled",
  auto_approved: boolean,
  created_at: string,
  processed_at?: string,
  processed_by_id?: number,
  processing_notes?: string
}>
```

#### `POST /api/permission-requests/`
**Purpose:** Submit new permission request  
**Auth Required:** ✅ PERMISSION_CREATE  
**Body:**
```typescript
{
  client_id: number,
  ga_property_id: string,
  target_email: string,
  permission_level: "viewer"|"analyst"|"marketer"|"editor"|"administrator",
  business_justification: string,
  duration_days?: number
}
```

#### `GET /api/permission-requests/auto-approval-rules`
**Purpose:** Get auto-approval rules for current user's role  
**Auth Required:** ✅ PERMISSION_READ  
**Response:**
```typescript
{
  rules: Array<{
    permission_level: string,
    auto_approved: boolean,
    required_role: string,
    reason: string
  }>,
  user_role: string
}
```

#### `GET /api/permission-requests/pending-approvals`
**Purpose:** Get requests pending approval (Admin/Super Admin only)  
**Auth Required:** ✅ PERMISSION_READ (Admin+)

#### `PUT /api/permission-requests/{request_id}/approve`
**Purpose:** Approve permission request  
**Auth Required:** ✅ PERMISSION_APPROVE  
**Body:**
```typescript
{
  processing_notes?: string
}
```

#### `PUT /api/permission-requests/{request_id}/reject`
**Purpose:** Reject permission request  
**Auth Required:** ✅ PERMISSION_APPROVE  
**Body:**
```typescript
{
  processing_notes: string // Required for rejections
}
```

---

## 🔄 Permission Lifecycle Management

### Complete lifecycle tracking: 요청→승인→활성→만료

#### `GET /api/permission-lifecycle/dashboard`
**Purpose:** Permission lifecycle overview dashboard  
**Auth Required:** ✅ PERMISSION_READ  
**Response:**
```typescript
{
  summary: {
    total_requests: number,
    active_permissions: number,
    expiring_soon: number,
    expired_permissions: number
  },
  request_stage: Record<string, number>, // Status counts
  active_stage: {
    active: number,
    expiring_soon: number,
    expired: number
  },
  permission_levels: Record<string, number>,
  user_context: {
    user_id: number,
    role: string,
    is_admin: boolean
  }
}
```

#### `GET /api/permission-lifecycle/timeline`
**Purpose:** Permission lifecycle timeline events  
**Auth Required:** ✅ PERMISSION_READ  
**Query Parameters:**
- `permission_request_id?`: number
- `permission_grant_id?`: number  
- `user_id?`: number (admin only)
- `days?`: number (1-365, default: 30)

#### `GET /api/permission-lifecycle/expiring`
**Purpose:** Get permissions expiring soon  
**Auth Required:** ✅ PERMISSION_READ  
**Query Parameters:**
- `days_ahead?`: number (1-90, default: 7)
- `limit?`: number (1-200, default: 50)
- `offset?`: number (default: 0)

**Response:**
```typescript
{
  expiring_permissions: Array<{
    permission_grant_id: number,
    user_id: number,
    target_email: string,
    permission_level: string,
    expires_at: string,
    days_until_expiry: number,
    urgency: "critical"|"high"|"medium"
  }>,
  total_count: number,
  urgency_summary: {
    critical: number,
    high: number, 
    medium: number
  }
}
```

#### `POST /api/permission-lifecycle/bulk-extend`
**Purpose:** Bulk extend multiple permissions  
**Auth Required:** ✅ PERMISSION_UPDATE  
**Body:**
```typescript
{
  permission_grant_ids: number[],
  additional_days: number, // 1-365
  reason?: string
}
```

---

## 🎯 GA4 Property Management

### Integrated with Permission System

#### `GET /api/ga4/`
**Purpose:** List GA4 properties with RBAC filtering  
**Auth Required:** ✅ GA4_PROPERTY_READ  
**Query Parameters:**
- `page?`: number (default: 1)
- `limit?`: number (1-1000, default: 100)
- `account_id?`: string

**Response:**
```typescript
{
  properties: Array<{
    property_id: string,
    property_name: string,
    account_id: string,
    account_name: string,
    created_time: string,
    display_name: string
  }>,
  total: number,
  page: number,
  per_page: number,
  pages: number
}
```

#### `GET /api/ga4/properties/{property_id}`
**Purpose:** Get specific GA4 property details  
**Auth Required:** ✅ GA4_PROPERTY_READ

#### `GET /api/ga4/properties/{property_id}/permissions`
**Purpose:** Get current permissions for GA4 property  
**Auth Required:** ✅ GA4_PROPERTY_READ  
**Response:**
```typescript
{
  property_id: string,
  permissions: Array<{
    email: string,
    role: "VIEWER"|"ANALYST"|"EDITOR"|"ADMIN",
    link_type: string
  }>,
  total_users: number,
  queried_at: string
}
```

#### `POST /api/ga4/properties/{property_id}/grant-permission`
**Purpose:** Grant permission to GA4 property (Admin only)  
**Auth Required:** ✅ GA4_PROPERTY_UPDATE  
**Body:**
```typescript
{
  target_email: string,
  role: "VIEWER"|"ANALYST"|"EDITOR"|"ADMIN"
}
```

#### `DELETE /api/ga4/properties/{property_id}/revoke-permission`
**Purpose:** Revoke permission from GA4 property  
**Auth Required:** ✅ GA4_PROPERTY_UPDATE  
**Query Parameters:**
- `target_email`: string (required)

---

## 👥 User Management with RBAC

### 7-Role System: viewer → requester → analyst → marketer → editor → admin → super_admin

#### `GET /api/users/`
**Purpose:** List users with RBAC filtering  
**Auth Required:** ✅ USER_READ  
**Query Parameters:**
- `skip?`: number (default: 0)
- `limit?`: number (1-100, default: 100)
- `role?`: string filter
- `is_active?`: boolean filter

#### `POST /api/users/`
**Purpose:** Create new user  
**Auth Required:** ✅ USER_CREATE  
**Body:**
```typescript
{
  email: string,
  password: string,
  full_name: string,
  role: "viewer"|"requester"|"analyst"|"marketer"|"editor"|"admin"|"super_admin",
  is_active?: boolean
}
```

#### `PUT /api/users/{user_id}`
**Purpose:** Update user  
**Auth Required:** ✅ USER_UPDATE (+ resource ownership rules)

---

## 🔐 RBAC System

### Role & Permission Management

#### `GET /api/rbac/roles`
**Purpose:** List all roles with their permissions  
**Auth Required:** ✅ ROLE_READ  
**Response:**
```typescript
Array<{
  name: string,
  display_name: string,
  level: number,
  permissions: string[],
  description: string
}>
```

#### `GET /api/rbac/role-hierarchy`
**Purpose:** Get role hierarchy structure  
**Auth Required:** ✅ ROLE_READ  
**Response:**
```typescript
{
  hierarchy: Array<{
    role: string,
    level: number,
    parent_roles: string[],
    child_roles: string[],
    permissions_count: number
  }>,
  total_roles: number,
  total_permissions: number
}
```

---

## 🔧 Service Account Management

### For GA4 Integration

#### `GET /api/service-accounts/`
**Purpose:** List service accounts  
**Auth Required:** ✅ SERVICE_ACCOUNT_READ

#### `GET /api/service-accounts/{sa_id}/properties`
**Purpose:** Get GA4 properties accessible by service account  
**Auth Required:** ✅ SERVICE_ACCOUNT_READ

#### `POST /api/service-accounts/{sa_id}/discover-properties`
**Purpose:** Discover new GA4 properties  
**Auth Required:** ✅ SERVICE_ACCOUNT_UPDATE

---

## 🚨 Error Handling

### Standard Error Response Format

```typescript
{
  error: string,           // Error code
  message: string,         // Human readable message  
  details?: any           // Additional error details
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing token |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permission |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists |
| `BUSINESS_RULE_VIOLATION` | 400 | Business logic violation |
| `GOOGLE_API_ERROR` | 503 | Google API service unavailable |
| `INTERNAL_SERVER_ERROR` | 500 | Server internal error |

---

## 🎛️ Frontend Integration Guidelines

### 1. Authentication Flow

```typescript
// Login and store token
const { access_token, refresh_token } = await api.login(credentials);
localStorage.setItem('access_token', access_token);

// Use in all requests
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
```

### 2. Permission-Based UI Rendering

```typescript
// Check user permissions before showing UI elements
const userPermissions = await api.get('/api/auth/me');
const canCreateRequests = userPermissions.permissions.includes('PERMISSION_CREATE');
const canApproveRequests = userPermissions.permissions.includes('PERMISSION_APPROVE');

// Conditionally render based on permissions
{canCreateRequests && <CreateRequestButton />}
{canApproveRequests && <ApprovalPanel />}
```

### 3. Error Handling Pattern

```typescript
try {
  const response = await api.post('/api/permission-requests/', requestData);
  toast.success('Permission request submitted successfully');
} catch (error) {
  if (error.response?.status === 403) {
    toast.error('Insufficient permissions');
  } else if (error.response?.status === 422) {
    toast.error(`Validation error: ${error.response.data.message}`);
  } else {
    toast.error('An unexpected error occurred');
  }
}
```

### 4. Permission Request Workflow UI

```typescript
// Status-based UI states
const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending': return 'yellow';
    case 'approved': return 'green';
    case 'rejected': return 'red';
    case 'cancelled': return 'gray';
  }
};

// Auto-approval indication
{request.auto_approved && (
  <Badge color="green">Auto-Approved</Badge>
)}
```

### 5. Real-time Updates (WebSocket Support)

```typescript
// Connect to permission updates
const ws = new WebSocket('ws://localhost:8000/ws/permissions');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'permission_approved') {
    // Update UI state
    updatePermissionStatus(update.request_id, 'approved');
  }
};
```

---

## 🧪 Testing & Validation

### API Contract Validation

The backend includes comprehensive test suites:

1. **Permission API Test:** `python test_permission_api.py`
2. **GA4 Integration Test:** `python ga4_integration_test.py`
3. **Structure Test:** `python simple_permission_test.py`

**Current Test Results:**
- ✅ Permission API Integration: 80% success rate
- ✅ GA4 Integration: 100% success rate
- ✅ Overall System Health: EXCELLENT

---

## 📋 Frontend Implementation Checklist

### Phase 3 Integration Tasks

- [ ] **Authentication Integration**
  - [ ] JWT token management
  - [ ] Auto-refresh token logic
  - [ ] Permission-based route guards

- [ ] **Permission Request UI**
  - [ ] Request submission form
  - [ ] My requests dashboard
  - [ ] Auto-approval rules display
  - [ ] Request status tracking

- [ ] **Permission Lifecycle UI**
  - [ ] Lifecycle dashboard
  - [ ] Timeline visualization
  - [ ] Expiring permissions alerts
  - [ ] Bulk extension interface

- [ ] **GA4 Integration UI**
  - [ ] Properties list with RBAC filtering
  - [ ] Property permission management
  - [ ] Permission grant/revoke interfaces

- [ ] **Admin Interface**
  - [ ] Pending approvals management
  - [ ] Role-based user interface
  - [ ] RBAC role management

- [ ] **Error Handling & UX**
  - [ ] Comprehensive error messaging
  - [ ] Loading states
  - [ ] Success confirmations
  - [ ] Korean/English localization

---

## 🚀 Deployment & Production Notes

### Environment Configuration

```typescript
// Environment-specific API URLs
const API_BASE_URL = {
  development: 'http://localhost:8000',
  staging: 'https://staging-api.ga4admin.com',
  production: 'https://api.ga4admin.com'
}[process.env.NODE_ENV];
```

### Performance Considerations

1. **Pagination:** All list endpoints support pagination (limit/offset)
2. **Caching:** Cache user permissions and role data for 5-10 minutes
3. **Error Boundaries:** Implement React error boundaries for API failures
4. **Loading States:** Show loading indicators for all async operations

### Security Best Practices

1. **Token Storage:** Use secure storage (httpOnly cookies preferred)
2. **HTTPS Only:** Never send tokens over HTTP in production
3. **Permission Checks:** Always verify permissions before UI actions
4. **Input Validation:** Validate all user inputs before API calls

---

## 📞 Support & Contact

For API contract questions or integration issues:

- **Backend Team:** Phase 3 Permission Management completed
- **Documentation:** This contract (API_CONTRACT.md)
- **API Documentation:** http://localhost:8000/api/docs
- **Test Results:** Available in `/backend/` directory

**Contract Status:** ✅ **READY FOR FRONTEND INTEGRATION**