# Permission Management API Contracts
## Frontend Permission Management Interface 통합 가이드

**Generated:** `2025-01-05T19:30:00Z`  
**Version:** `3.0.0`  
**Phase:** `Phase 3 - Permission Management System`

---

## 📋 Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Permission Request Workflow](#permission-request-workflow)
3. [GA4 Property Integration](#ga4-property-integration)
4. [Permission Lifecycle Management](#permission-lifecycle-management)
5. [Notification System](#notification-system)
6. [API Endpoints Reference](#api-endpoints-reference)
7. [Frontend Integration Guidelines](#frontend-integration-guidelines)
8. [Error Handling](#error-handling)
9. [Testing Scenarios](#testing-scenarios)

---

## 🏗️ Overview & Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────┐
│                   Frontend UI                       │
├─────────────────────────────────────────────────────┤
│              Permission Management API              │
├─────────────────────────────────────────────────────┤
│                    Backend Services                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ Permission  │ │     GA4     │ │ Lifecycle   │   │
│  │  Requests   │ │ Properties  │ │ Management  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
├─────────────────────────────────────────────────────┤
│               Database & External APIs              │
└─────────────────────────────────────────────────────┘
```

### Core Components
- **Permission Requests**: 사용자 권한 요청 및 승인 워크플로우
- **GA4 Properties**: Google Analytics 4 속성별 권한 관리
- **Lifecycle Management**: 권한 생명주기 추적 (요청→승인→활성→만료)
- **Notification System**: 실시간 알림 및 이메일 통지

---

## 🔄 Permission Request Workflow

### 1. Permission Request Creation

**Endpoint:** `POST /api/permission-requests/`

**Request Body:**
```json
{
  "client_id": 1,
  "ga_property_id": "properties/123456789",
  "target_email": "user@example.com",
  "permission_level": "VIEWER",
  "business_justification": "Need access for monthly reporting",
  "requested_duration_days": 30
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 5,
  "client_id": 1,
  "ga_property_id": "properties/123456789",
  "target_email": "user@example.com",
  "permission_level": "VIEWER",
  "status": "APPROVED",
  "business_justification": "Need access for monthly reporting",
  "requested_duration_days": 30,
  "auto_approved": true,
  "requires_approval_from_role": null,
  "processed_at": "2025-01-05T19:30:00Z",
  "processed_by_id": null,
  "processing_notes": "Auto-approved based on user role and permission level",
  "permission_grant_id": 15,
  "created_at": "2025-01-05T19:30:00Z",
  "updated_at": "2025-01-05T19:30:00Z"
}
```

### 2. Auto-Approval Rules Query

**Endpoint:** `GET /api/permission-requests/auto-approval-rules`

**Response:**
```json
{
  "rules": [
    {
      "permission_level": "VIEWER",
      "user_role": "REQUESTER",
      "auto_approved": true,
      "requires_approval_from_role": null,
      "reason": "Viewer permissions are auto-approved for Requester+ roles"
    },
    {
      "permission_level": "EDITOR",
      "user_role": "REQUESTER", 
      "auto_approved": false,
      "requires_approval_from_role": "ADMIN",
      "reason": "Editor permissions require Admin approval"
    }
  ],
  "user_role": "REQUESTER"
}
```

### 3. User's Permission Requests

**Endpoint:** `GET /api/permission-requests/my-requests?status=PENDING&limit=20`

**Response:**
```json
[
  {
    "id": 2,
    "user_id": 5,
    "client_id": 1,
    "ga_property_id": "properties/987654321",
    "target_email": "user@example.com",
    "permission_level": "EDITOR",
    "status": "PENDING",
    "business_justification": "Need editor access for campaign optimization",
    "requested_duration_days": 60,
    "auto_approved": false,
    "requires_approval_from_role": "ADMIN",
    "processed_at": null,
    "processed_by_id": null,
    "processing_notes": null,
    "permission_grant_id": null,
    "created_at": "2025-01-05T18:00:00Z",
    "updated_at": "2025-01-05T18:00:00Z"
  }
]
```

### 4. Admin Approval Workflow

**Endpoint:** `GET /api/permission-requests/pending-approvals?limit=50`

**Response (Admin/Super Admin only):**
```json
[
  {
    "id": 2,
    "user_id": 5,
    "client_id": 1,
    "ga_property_id": "properties/987654321",
    "target_email": "user@example.com",
    "permission_level": "EDITOR",
    "status": "PENDING",
    "business_justification": "Need editor access for campaign optimization",
    "requires_approval_from_role": "ADMIN",
    "user": {
      "id": 5,
      "email": "requester@example.com",
      "name": "John Requester"
    },
    "client": {
      "id": 1,
      "name": "Acme Corporation"
    }
  }
]
```

**Approval Action:** `PUT /api/permission-requests/2/approve`

**Request Body:**
```json
{
  "processing_notes": "Approved for Q1 campaign optimization project"
}
```

---

## 🎯 GA4 Property Integration

### 1. Client Properties Discovery

**Endpoint:** `GET /api/permission-requests/clients/1/properties`

**Response:**
```json
{
  "client_id": 1,
  "client_name": "Acme Corporation",
  "service_accounts": [
    {
      "id": 3,
      "email": "sa-analytics@acme-project.iam.gserviceaccount.com",
      "display_name": "Acme Analytics Service Account",
      "is_active": true,
      "health_status": "HEALTHY",
      "properties": [
        {
          "id": 1,
          "service_account_id": 3,
          "ga_property_id": "properties/123456789",
          "property_name": "Acme Website",
          "property_account_id": "accounts/123456",
          "is_active": true,
          "validation_status": "VALID",
          "last_validated_at": "2025-01-05T12:00:00Z"
        }
      ]
    }
  ],
  "total_properties": 5
}
```

### 2. GA4 Property Management

**List Properties:** `GET /api/ga4/?page=1&limit=20&account_id=accounts/123456`

**Response:**
```json
{
  "properties": [
    {
      "id": "properties/123456789",
      "name": "Acme Website",
      "account_id": "accounts/123456",
      "display_name": "Acme Website (ID: 123456789)",
      "time_zone": "Asia/Seoul",
      "currency_code": "KRW"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

### 3. Property Permissions Management

**Get Property Permissions:** `GET /api/ga4/properties/123456789/permissions`

**Response:**
```json
{
  "property_id": "properties/123456789",
  "permissions": [
    {
      "email": "admin@example.com",
      "roles": ["ADMIN"],
      "direct_roles": ["ADMIN"],
      "inherited_roles": []
    },
    {
      "email": "user@example.com", 
      "roles": ["VIEWER"],
      "direct_roles": ["VIEWER"],
      "inherited_roles": []
    }
  ],
  "total_users": 2,
  "queried_at": "2025-01-05T19:30:00Z",
  "queried_by": 1
}
```

**Grant Property Permission:** `POST /api/ga4/properties/123456789/grant-permission`

**Request Body:**
```json
{
  "target_email": "newuser@example.com",
  "role": "VIEWER"
}
```

**Response:**
```json
{
  "property_id": "properties/123456789",
  "target_email": "newuser@example.com",
  "role": "VIEWER",
  "granted_at": "2025-01-05T19:30:00Z",
  "granted_by": 1,
  "google_api_result": {
    "binding_name": "properties/123456789/bindings/viewer_binding_12345",
    "status": "SUCCESS"
  }
}
```

---

## 📊 Permission Lifecycle Management

### 1. Lifecycle Dashboard

**Endpoint:** `GET /api/permission-lifecycle/dashboard`

**Response:**
```json
{
  "summary": {
    "total_requests": 45,
    "active_permissions": 23,
    "expiring_soon": 3,
    "expired_permissions": 8
  },
  "request_stage": {
    "PENDING": 5,
    "APPROVED": 35,
    "REJECTED": 3,
    "CANCELLED": 2
  },
  "active_stage": {
    "active": 23,
    "expiring_soon": 3,
    "expired": 8
  },
  "permission_levels": {
    "VIEWER": 15,
    "ANALYST": 8,
    "MARKETER": 0,
    "EDITOR": 0,
    "ADMINISTRATOR": 0
  },
  "generated_at": "2025-01-05T19:30:00Z",
  "user_context": {
    "user_id": 5,
    "role": "REQUESTER",
    "is_admin": false
  }
}
```

### 2. Permission Timeline

**Endpoint:** `GET /api/permission-lifecycle/timeline?days=30&limit=50`

**Response:**
```json
{
  "timeline": [
    {
      "id": "req_15_created",
      "type": "request_created",
      "stage": "요청",
      "timestamp": "2025-01-05T19:30:00Z",
      "permission_request_id": 15,
      "user_id": 5,
      "ga_property_id": "properties/123456789",
      "permission_level": "VIEWER",
      "status": "APPROVED",
      "description": "Permission request created for user@example.com",
      "details": {
        "target_email": "user@example.com",
        "business_justification": "Monthly reporting access",
        "auto_approved": true
      }
    },
    {
      "id": "grant_20_activated",
      "type": "permission_activated",
      "stage": "활성",
      "timestamp": "2025-01-05T19:30:00Z",
      "permission_grant_id": 20,
      "user_id": 5,
      "ga_property_id": "properties/123456789",
      "permission_level": "VIEWER",
      "target_email": "user@example.com",
      "description": "Permission activated for user@example.com",
      "details": {
        "expires_at": "2025-02-05T19:30:00Z",
        "approved_by_id": null
      }
    }
  ],
  "total_events": 15,
  "date_range": {
    "start": "2024-12-06T19:30:00Z",
    "end": "2025-01-05T19:30:00Z",
    "days": 30
  },
  "stage_summary": {
    "요청": 8,
    "승인": 5,
    "활성": 2
  }
}
```

### 3. Expiring Permissions

**Endpoint:** `GET /api/permission-lifecycle/expiring?days_ahead=7&limit=20`

**Response:**
```json
{
  "expiring_permissions": [
    {
      "permission_grant_id": 18,
      "user_id": 5,
      "client_id": 1,
      "ga_property_id": "properties/123456789",
      "target_email": "user@example.com",
      "permission_level": "VIEWER",
      "expires_at": "2025-01-08T10:00:00Z",
      "days_until_expiry": 2,
      "hours_until_expiry": 62.5,
      "urgency": "high",
      "can_extend": true,
      "created_at": "2024-12-09T10:00:00Z",
      "approved_at": "2024-12-09T10:00:00Z"
    }
  ],
  "total_count": 3,
  "returned_count": 1,
  "urgency_summary": {
    "critical": 0,
    "high": 1,
    "medium": 2
  },
  "query_parameters": {
    "days_ahead": 7,
    "threshold_date": "2025-01-12T19:30:00Z"
  }
}
```

### 4. Bulk Extension

**Endpoint:** `POST /api/permission-lifecycle/bulk-extend`

**Request Body:**
```json
{
  "permission_grant_ids": [18, 19, 20],
  "additional_days": 30,
  "reason": "Extended for Q1 2025 reporting cycle"
}
```

**Response:**
```json
{
  "extended": [
    {
      "permission_grant_id": 18,
      "additional_days": 30,
      "new_expires_at": "2025-02-07T10:00:00Z",
      "extended_by": 1,
      "reason": "Extended for Q1 2025 reporting cycle"
    }
  ],
  "failed": [],
  "summary": {
    "total_requested": 3,
    "successful": 3,
    "failed": 0
  }
}
```

---

## 🔔 Notification System

### 1. Notification Triggers

| Event | Description | Recipients | Channel |
|-------|-------------|------------|---------|
| **Request Created** | 새로운 권한 요청 생성 | 요청자, 승인자 | Email + In-App |
| **Auto Approved** | 자동 승인 완료 | 요청자 | Email + In-App |
| **Pending Approval** | 승인 대기 중 | 승인자 | Email + In-App |
| **Request Approved** | 권한 요청 승인 | 요청자 | Email + In-App |
| **Request Rejected** | 권한 요청 거부 | 요청자 | Email + In-App |
| **Permission Activated** | 권한 활성화 완료 | 요청자, 대상자 | Email |
| **Expiry Warning** | 만료 7일 전 경고 | 요청자, 대상자 | Email + In-App |
| **Permission Expired** | 권한 만료 | 요청자, 대상자 | Email |

### 2. Notification Templates

**Permission Request Created:**
```json
{
  "template_type": "permission_request_created",
  "subject": "[GA4 Admin] New permission request submitted",
  "variables": {
    "requester_name": "John Requester",
    "target_email": "user@example.com",
    "property_name": "Acme Website",
    "permission_level": "VIEWER",
    "business_justification": "Monthly reporting access",
    "auto_approved": true,
    "dashboard_url": "https://ga4admin.example.com/dashboard/requests"
  }
}
```

**Permission Expiring Soon:**
```json
{
  "template_type": "permission_expiring_warning",
  "subject": "[GA4 Admin] Permission expiring in 7 days",
  "variables": {
    "target_email": "user@example.com",
    "property_name": "Acme Website",
    "expires_at": "2025-01-12T10:00:00Z",
    "days_remaining": 7,
    "extension_url": "https://ga4admin.example.com/dashboard/permissions/18/extend"
  }
}
```

---

## 📚 API Endpoints Reference

### Permission Requests
- `POST /api/permission-requests/` - Create permission request
- `GET /api/permission-requests/my-requests` - Get user's requests
- `GET /api/permission-requests/pending-approvals` - Get pending approvals (Admin)
- `GET /api/permission-requests/auto-approval-rules` - Get auto-approval rules
- `PUT /api/permission-requests/{id}/approve` - Approve request
- `PUT /api/permission-requests/{id}/reject` - Reject request
- `GET /api/permission-requests/{id}` - Get specific request
- `DELETE /api/permission-requests/{id}` - Cancel pending request

### GA4 Properties
- `GET /api/ga4/` - List GA4 properties
- `GET /api/ga4/properties/{property_id}` - Get property details
- `GET /api/ga4/properties/{property_id}/permissions` - Get property permissions
- `POST /api/ga4/properties/{property_id}/grant-permission` - Grant permission
- `DELETE /api/ga4/properties/{property_id}/revoke-permission` - Revoke permission
- `GET /api/permission-requests/clients/{client_id}/properties` - Get client properties

### Permission Lifecycle
- `GET /api/permission-lifecycle/dashboard` - Lifecycle dashboard
- `GET /api/permission-lifecycle/timeline` - Permission timeline
- `GET /api/permission-lifecycle/expiring` - Expiring permissions
- `POST /api/permission-lifecycle/bulk-extend` - Bulk extend permissions
- `GET /api/permission-lifecycle/lifecycle-stats` - Lifecycle statistics

---

## 🎨 Frontend Integration Guidelines

### 1. Permission Request Form

**Component Requirements:**
```tsx
interface PermissionRequestFormProps {
  userClients: Client[];
  onSubmit: (data: PermissionRequestCreate) => Promise<void>;
  autoApprovalRules: AutoApprovalRule[];
}

interface PermissionRequestForm {
  // Client selection with properties lookup
  client_id: number;
  available_properties: ServiceAccountProperty[];
  
  // GA4 property selection
  ga_property_id: string;
  property_display_name: string;
  
  // Permission details
  target_email: string;
  permission_level: PermissionLevel;
  business_justification: string;
  requested_duration_days: number;
  
  // Auto-approval preview
  will_auto_approve: boolean;
  requires_approval_from: UserRole | null;
}
```

### 2. Permission Dashboard

**Dashboard Widgets:**
```tsx
interface PermissionDashboard {
  lifecycleSummary: LifecycleSummaryWidget;
  recentRequests: RecentRequestsWidget;
  expiringPermissions: ExpiringPermissionsWidget;
  timelineView: TimelineWidget;
  bulkActions: BulkActionsPanel;
}

interface LifecycleSummaryWidget {
  totalRequests: number;
  activePermissions: number;
  expiringSoon: number;
  expiredPermissions: number;
  stageBreakdown: Record<string, number>;
}
```

### 3. Admin Approval Interface

**Approval Queue:**
```tsx
interface ApprovalQueue {
  pendingRequests: PendingRequest[];
  filters: {
    permission_level: PermissionLevel[];
    client_id: number[];
    urgency: string[];
  };
  bulkActions: {
    approve: (ids: number[], notes?: string) => Promise<void>;
    reject: (ids: number[], reason: string) => Promise<void>;
  };
}

interface PendingRequest {
  id: number;
  requesterInfo: UserInfo;
  clientInfo: ClientInfo;
  permissionDetails: PermissionDetails;
  urgencyLevel: 'low' | 'medium' | 'high' | 'critical';
  businessJustification: string;
  quickActions: ApprovalActions;
}
```

### 4. Real-time Updates

**WebSocket Integration:**
```tsx
// Subscribe to permission updates
const usePermissionUpdates = (userId: number) => {
  const [updates, setUpdates] = useState<PermissionUpdate[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket(`wss://api.example.com/ws/permissions/${userId}`);
    
    ws.onmessage = (event) => {
      const update: PermissionUpdate = JSON.parse(event.data);
      setUpdates(prev => [update, ...prev]);
      
      // Show notification
      showNotification({
        type: update.type,
        message: update.message,
        action: update.action_url
      });
    };
    
    return () => ws.close();
  }, [userId]);
  
  return updates;
};
```

---

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid permission request data",
  "details": {
    "field": "target_email",
    "code": "INVALID_EMAIL_FORMAT",
    "description": "Email format is invalid"
  },
  "timestamp": "2025-01-05T19:30:00Z",
  "request_id": "req_12345"
}
```

### Common Error Codes

| Code | HTTP Status | Description | User Action |
|------|-------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed | Fix form data |
| `UNAUTHORIZED` | 401 | Authentication required | Login again |
| `FORBIDDEN` | 403 | Insufficient permissions | Contact admin |
| `NOT_FOUND` | 404 | Resource not found | Check resource exists |
| `CONFLICT` | 409 | Duplicate request | Use existing request |
| `GOOGLE_API_ERROR` | 503 | Google API unavailable | Retry later |

### Frontend Error Handling

```tsx
const handlePermissionRequest = async (data: PermissionRequestCreate) => {
  try {
    const response = await api.post('/permission-requests/', data);
    showSuccessMessage('Permission request submitted successfully');
    
    if (response.data.auto_approved) {
      showInfoMessage('Request was auto-approved and is now active');
    } else {
      showInfoMessage(`Request pending approval from ${response.data.requires_approval_from_role}`);
    }
  } catch (error) {
    if (error.response?.status === 409) {
      showErrorMessage('A similar request already exists');
    } else if (error.response?.status === 403) {
      showErrorMessage('You do not have permission to request access to this property');
    } else {
      showErrorMessage('An error occurred while submitting your request');
    }
  }
};
```

---

## 🧪 Testing Scenarios

### 1. Permission Request Flow Tests

**Test Case 1: Auto-Approved Request**
```javascript
describe('Auto-Approved Permission Request', () => {
  it('should auto-approve VIEWER permission for REQUESTER role', async () => {
    const requestData = {
      client_id: 1,
      ga_property_id: 'properties/123456789',
      target_email: 'user@example.com',
      permission_level: 'VIEWER',
      business_justification: 'Monthly reporting',
      requested_duration_days: 30
    };
    
    const response = await request(app)
      .post('/api/permission-requests/')
      .set('Authorization', `Bearer ${requesterToken}`)
      .send(requestData)
      .expect(201);
    
    expect(response.body.auto_approved).toBe(true);
    expect(response.body.status).toBe('APPROVED');
    expect(response.body.permission_grant_id).toBeDefined();
  });
});
```

**Test Case 2: Admin Approval Required**
```javascript
describe('Admin Approval Required', () => {
  it('should require admin approval for EDITOR permission', async () => {
    const requestData = {
      client_id: 1,
      ga_property_id: 'properties/123456789',
      target_email: 'user@example.com',
      permission_level: 'EDITOR',
      business_justification: 'Campaign optimization',
      requested_duration_days: 60
    };
    
    const response = await request(app)
      .post('/api/permission-requests/')
      .set('Authorization', `Bearer ${requesterToken}`)
      .send(requestData)
      .expect(201);
    
    expect(response.body.auto_approved).toBe(false);
    expect(response.body.status).toBe('PENDING');
    expect(response.body.requires_approval_from_role).toBe('ADMIN');
  });
});
```

### 2. GA4 Integration Tests

**Test Case 3: Property Permissions Management**
```javascript
describe('GA4 Property Permissions', () => {
  it('should grant property permission successfully', async () => {
    const grantData = {
      target_email: 'newuser@example.com',
      role: 'VIEWER'
    };
    
    const response = await request(app)
      .post('/api/ga4/properties/123456789/grant-permission')
      .set('Authorization', `Bearer ${adminToken}`)
      .send(grantData)
      .expect(200);
    
    expect(response.body.target_email).toBe('newuser@example.com');
    expect(response.body.role).toBe('VIEWER');
    expect(response.body.google_api_result.status).toBe('SUCCESS');
  });
});
```

### 3. Lifecycle Management Tests

**Test Case 4: Expiring Permissions**
```javascript
describe('Permission Lifecycle', () => {
  it('should identify permissions expiring soon', async () => {
    const response = await request(app)
      .get('/api/permission-lifecycle/expiring?days_ahead=7')
      .set('Authorization', `Bearer ${adminToken}`)
      .expect(200);
    
    expect(response.body.expiring_permissions).toBeInstanceOf(Array);
    response.body.expiring_permissions.forEach(permission => {
      expect(permission.days_until_expiry).toBeLessThanOrEqual(7);
      expect(permission.urgency).toBeOneOf(['critical', 'high', 'medium']);
    });
  });
});
```

---

## 📈 Performance Considerations

### 1. API Response Optimization
- **Pagination**: All list endpoints support `limit` and `offset` parameters
- **Filtering**: Use query parameters to reduce response size
- **Field Selection**: Consider implementing field selection for large objects
- **Caching**: Implement appropriate caching headers for static data

### 2. Real-time Updates
- **WebSocket**: Use WebSocket connections for real-time permission updates
- **Polling**: Fallback to polling for browsers without WebSocket support
- **Rate Limiting**: Implement rate limiting to prevent API abuse

### 3. Frontend Performance
- **Virtual Scrolling**: For large lists of permissions or requests
- **Debounced Search**: Implement debounced search for property lookups
- **Lazy Loading**: Load permission details on demand
- **Optimistic Updates**: Update UI immediately, handle errors gracefully

---

## 🔐 Security Considerations

### 1. Authentication & Authorization
- All endpoints require valid JWT authentication
- Role-based access control enforced at API level
- Resource ownership validation for non-admin users

### 2. Data Validation
- Input validation on all request parameters
- SQL injection prevention through parameterized queries
- XSS protection through output encoding

### 3. Audit Logging
- All permission-related actions are logged
- Audit trails include actor, action, resource, and timestamp
- Logs are tamper-evident and retained per compliance requirements

---

This comprehensive API contract provides everything needed for the Frontend team to build a complete Permission Management Interface. The system supports the full permission lifecycle from request creation through expiry management, with proper notification and audit capabilities.