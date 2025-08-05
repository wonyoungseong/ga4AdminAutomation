# GA4 Admin Automation System - RBAC API Contracts

## 🛡️ Role-Based Access Control (RBAC) API Specification

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: TBD

## 👥 User Roles & Hierarchy

### Role Hierarchy (Highest to Lowest)
1. **SUPER_ADMIN** (Level 4) - Full system administration
2. **ADMIN** (Level 3) - User and client management  
3. **REQUESTER** (Level 2) - Permission requests and profile management
4. **VIEWER** (Level 1) - Read-only access

### Role Management Rules
- Higher-level roles can manage lower-level users
- Users cannot demote their own role
- Only SUPER_ADMIN can assign SUPER_ADMIN role
- Role changes require appropriate permissions

---

## 🔐 Enhanced User Management APIs

### 1. List Users (Protected)
```http
GET /api/users/?limit=50&offset=0&role=REQUESTER&status=active
Authorization: Bearer {access_token}
```

**Required Permissions**: `read_user` (ADMIN+ only)

**Response (200)**:
```json
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "REQUESTER",
      "status": "active",
      "created_at": "2025-08-05T14:20:14",
      "last_login_at": "2025-08-05T15:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

### 2. Create User (Protected)
```http
POST /api/users/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepass123",
  "name": "New User",
  "role": "REQUESTER",
  "company": "Example Corp"
}
```

**Required Permissions**: `create_user` (ADMIN+ only)
**Role Validation**: Can only create roles at or below your hierarchy level

**Response (201)**:
```json
{
  "id": 2,
  "email": "newuser@example.com", 
  "name": "New User",
  "role": "REQUESTER",
  "status": "active",
  "created_at": "2025-08-05T16:00:00"
}
```

### 3. Get User Details (Protected)
```http
GET /api/users/{user_id}
Authorization: Bearer {access_token}
```

**Required Permissions**: `read_user` (ADMIN+ for others, own profile allowed)

**Response (200)**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe", 
  "role": "REQUESTER",
  "status": "active",
  "company": "Example Corp",
  "created_at": "2025-08-05T14:20:14",
  "last_login_at": "2025-08-05T15:30:00"
}
```

### 4. Update User (Protected)
```http
PUT /api/users/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Name",
  "company": "New Company"
}
```

**Required Permissions**: `update_user` (ADMIN+ for others, own profile allowed)

### 5. Delete User (Protected)
```http
DELETE /api/users/{user_id}
Authorization: Bearer {access_token}
```

**Required Permissions**: `delete_user` (SUPER_ADMIN only)
**Restrictions**: Cannot delete own account

**Response (200)**:
```json
{
  "message": "User 123 deleted successfully"
}
```

---

## 🎭 Role Assignment APIs

### 1. Assign Role to User
```http
PUT /api/users/{user_id}/role
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "role": "ADMIN"
}
```

**Required Permissions**: `change_user_role` (SUPER_ADMIN+ only)
**Validation**: 
- Can only assign roles at or below your hierarchy level
- Cannot demote your own role

**Response (200)**:
```json
{
  "message": "Role updated successfully",
  "user_id": 123,
  "previous_role": "REQUESTER", 
  "new_role": "ADMIN",
  "updated_by": 1
}
```

### 2. Get User Permissions
```http
GET /api/users/{user_id}/permissions
Authorization: Bearer {access_token}
```

**Required Permissions**: `read_user` (ADMIN+ for others, own permissions allowed)

**Response (200)**:
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "ADMIN",
  "permissions": [
    "create_user", "read_user", "update_user", "delete_user",
    "create_client", "read_client", "update_client", "delete_client",
    "manage_client_assignments", "read_assigned_client_assignments",
    "read_permission", "approve_permission", "reject_permission",
    "create_permission", "delete_permission",
    "read_audit_log", "read_filtered_audit_logs",
    "ga4_admin"
  ],
  "permission_count": 15,
  "can_manage_users": true,
  "can_manage_clients": true,
  "can_approve_permissions": true,
  "system_admin": false
}
```

### 3. Get Role Hierarchy
```http
GET /api/users/roles/hierarchy
Authorization: Bearer {access_token}
```

**Required Permissions**: `read_user` (All authenticated users)

**Response (200)**:
```json
{
  "roles": [
    {
      "name": "SUPER_ADMIN",
      "level": 4,
      "description": "Full system access with all permissions",
      "can_manage": ["SUPER_ADMIN", "ADMIN", "REQUESTER", "VIEWER"]
    },
    {
      "name": "ADMIN",
      "level": 3, 
      "description": "Administrative access for user and client management",
      "can_manage": ["REQUESTER", "VIEWER"]
    },
    {
      "name": "REQUESTER",
      "level": 2,
      "description": "Can request permissions and manage own profile", 
      "can_manage": []
    },
    {
      "name": "VIEWER",
      "level": 1,
      "description": "Read-only access to assigned data",
      "can_manage": []
    }
  ],
  "permissions_matrix": {
    "SUPER_ADMIN": 16,
    "ADMIN": 12,
    "REQUESTER": 6,
    "VIEWER": 4
  },
  "your_role": {
    "name": "ADMIN",
    "level": 3
  }
}
```

### 4. Get Manageable Roles
```http
GET /api/users/manageable-roles
Authorization: Bearer {access_token}
```

**Required Permissions**: `change_user_role` (ADMIN+)

**Response (200)**:
```json
{
  "your_role": "ADMIN",
  "manageable_roles": [
    {
      "name": "REQUESTER",
      "description": "Permission requests and profile management"
    },
    {
      "name": "VIEWER", 
      "description": "Read-only access"
    }
  ],
  "count": 2
}
```

---

## 🚨 Error Responses

### Authentication Errors
```json
{
  "detail": "Invalid token"
}
```

### Authorization Errors  
```json
{
  "detail": "Insufficient permissions. Missing: create_user"
}
```

### Role Assignment Errors
```json
{
  "detail": "Cannot assign role SUPER_ADMIN. Your role (ADMIN) has insufficient privileges."
}
```

### Self-Demotion Prevention
```json
{
  "detail": "Cannot demote your own role"
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "role"],
      "msg": "Invalid role: INVALID_ROLE",
      "input": "INVALID_ROLE"
    }
  ]
}
```

---

## 🎯 Frontend Implementation Guidelines

### 1. Role-Based UI Components
```javascript
// Example: Show/hide UI elements based on permissions
const userPermissions = usePermissions(); // Custom hook

const canCreateUsers = userPermissions.includes('create_user');
const canManageRoles = userPermissions.includes('change_user_role');

return (
  <div>
    {canCreateUsers && <CreateUserButton />}
    {canManageRoles && <RoleAssignmentPanel />}
  </div>
);
```

### 2. Permission Checking Utility
```javascript
// Utility function for permission checks
export const hasPermission = (userPermissions, requiredPermission) => {
  return userPermissions.includes(requiredPermission);
};

export const hasAnyPermission = (userPermissions, requiredPermissions) => {
  return requiredPermissions.some(permission => 
    userPermissions.includes(permission)
  );
};
```

### 3. Role Hierarchy Helpers
```javascript
// Helper functions for role management
export const canManageRole = (currentRole, targetRole) => {
  const hierarchy = {
    'SUPER_ADMIN': 4,
    'ADMIN': 3, 
    'REQUESTER': 2,
    'VIEWER': 1
  };
  
  return hierarchy[currentRole] > hierarchy[targetRole];
};

export const getRoleLevel = (role) => {
  const levels = {
    'SUPER_ADMIN': 4,
    'ADMIN': 3,
    'REQUESTER': 2, 
    'VIEWER': 1
  };
  return levels[role] || 0;
};
```

### 4. API Integration Examples
```javascript
// Role assignment
const assignRole = async (userId, newRole) => {
  try {
    const response = await fetch(`/api/users/${userId}/role`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ role: newRole })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Role assignment failed:', error.message);
    throw error;
  }
};

// Get user permissions
const getUserPermissions = async (userId) => {
  const response = await fetch(`/api/users/${userId}/permissions`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch permissions');
  }
  
  return await response.json();
};
```

---

## 🔒 Security Considerations

### 1. Token Validation
- All protected endpoints require valid JWT token
- Tokens expire after configured duration
- Use refresh tokens for session management

### 2. Permission Validation
- Server-side permission validation on every request
- Client-side checks for UI optimization only
- Never trust client-side permission logic alone

### 3. Role Assignment Security
- Hierarchical role validation prevents privilege escalation
- Self-demotion prevention maintains system integrity
- Audit logs track all role changes

### 4. Error Handling
- Consistent error response format
- Detailed error messages for development
- Generic error messages for production security

---

## 📊 Testing & Validation

### 1. Role-Based Test Scenarios
- Test each role's access to protected endpoints
- Verify permission inheritance in role hierarchy
- Test role assignment validation rules
- Validate self-demotion prevention

### 2. Frontend Testing
- Mock API responses for different user roles
- Test UI component visibility based on permissions
- Validate role assignment form restrictions
- Test error handling for insufficient permissions

### 3. Integration Testing
- End-to-end user workflows with different roles
- Role transition scenarios (promotion/demotion)
- Permission propagation across system components

---

**🎯 API Contract Status: Production Ready**
**📅 Last Updated**: August 5, 2025
**🔄 Version**: 2.0.0