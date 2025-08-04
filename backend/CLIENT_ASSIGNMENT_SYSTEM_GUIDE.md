# GA4 Admin Automation - Client Assignment & Access Control System

## Overview

This enhanced system implements a comprehensive client assignment and access control framework that ensures users can only access clients they are explicitly assigned to, while maintaining proper role-based hierarchical permissions.

## Key Features

### 🔐 Client-User Assignment System
- **Many-to-Many Relationships**: Users can be assigned to multiple clients, and clients can have multiple users
- **Assignment Metadata**: Track who assigned whom, when, expiration dates, and notes
- **Status Management**: Active, inactive, and suspended assignment states
- **Bulk Operations**: Efficiently manage multiple assignments at once

### 🛡️ Enhanced Access Control
- **Role-Based Hierarchy**: Super Admin > Admin > Requester > Viewer
- **Client-Level Isolation**: Users only see data for their assigned clients
- **Automatic Filtering**: All API endpoints automatically filter by accessible clients
- **Permission Validation**: Real-time access validation for all operations

### 📊 Comprehensive RBAC Integration
- **Super Admins**: Full system access to all clients and operations
- **Admins**: Manage users and clients, see assigned clients + system management
- **Requesters**: Access assigned clients, create permission requests
- **Viewers**: Read-only access to assigned clients and permissions

## Architecture

### Database Schema

```sql
-- Client Assignments Table
CREATE TABLE client_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    client_id INTEGER NOT NULL REFERENCES clients(id),
    assigned_by_id INTEGER NOT NULL REFERENCES users(id),
    status client_assignment_status DEFAULT 'active',
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX ix_client_assignments_user_id ON client_assignments(user_id);
CREATE INDEX ix_client_assignments_client_id ON client_assignments(client_id);
CREATE UNIQUE INDEX ix_client_assignments_unique_active 
    ON client_assignments(user_id, client_id) 
    WHERE status = 'active';
```

### Core Components

#### 1. Database Models (`src/models/db_models.py`)
- **ClientAssignment**: Core assignment model with relationships
- **Enhanced User/Client**: Added assignment relationships
- **AuditLog**: Extended with client assignment tracking

#### 2. Service Layer (`src/services/client_assignment_service.py`)
- **ClientAssignmentService**: Centralized assignment management
- **Access Control Logic**: User-client access validation
- **Bulk Operations**: Efficient multi-assignment handling

#### 3. API Layer (`src/api/routers/`)
- **client_assignments.py**: Assignment CRUD operations
- **clients_enhanced.py**: Client management with access control
- **permissions_enhanced.py**: Permission management with client filtering

#### 4. Authentication & Authorization (`src/core/auth_dependencies.py`)
- **Enhanced Dependencies**: Client access validation
- **Role-Based Decorators**: Permission requirement enforcement
- **Access Control Helpers**: Utility functions for access checks

## API Endpoints

### Client Assignment Management

#### Create Assignment
```http
POST /api/client-assignments/
Content-Type: application/json

{
    "user_id": 5,
    "client_id": 2,
    "status": "active",
    "expires_at": "2025-08-01T00:00:00Z",
    "notes": "Marketing campaign management"
}
```

#### Bulk Create Assignments
```http
POST /api/client-assignments/bulk
Content-Type: application/json

{
    "user_ids": [3, 4, 5],
    "client_ids": [1, 2],
    "status": "active",
    "notes": "Quarterly project assignments"
}
```

#### List User's Assignments
```http
GET /api/client-assignments/users/5/clients?include_inactive=false
```

#### List Client's Assignments
```http
GET /api/client-assignments/clients/2/users?include_inactive=true
```

### Enhanced Client Management

#### List Accessible Clients
```http
GET /api/clients/?page=1&per_page=10&include_inactive=false
```

#### Get Client with Users
```http
GET /api/clients/2?include_inactive_assignments=false
```

#### Get My Accessible Clients
```http
GET /api/clients/my/accessible?include_inactive=false
```

#### Quick Assign User to Client
```http
POST /api/clients/2/assign-user/5?notes=Project manager role
```

### Enhanced Permission Management

#### List Permissions with Access Control
```http
GET /api/permissions/?client_id=2&status=pending&page=1&per_page=20
```

#### Get My Permission Requests
```http
GET /api/permissions/my/requests?status=approved
```

#### Get Pending Permissions for Review
```http
GET /api/permissions/pending/review
```

### Access Control Validation

#### Validate Client Access
```http
POST /api/client-assignments/validate-access/2
```

#### Get Access Control Summary
```http
GET /api/client-assignments/access-control/5
```

#### Get My Accessible Clients
```http
GET /api/client-assignments/my/accessible-clients
```

## Access Control Rules

### Super Admin
- ✅ **Full Access**: All clients, users, and operations
- ✅ **No Restrictions**: Can manage any client assignment
- ✅ **System Operations**: Create/delete clients, manage all users

### Admin
- ✅ **Broad Access**: All active clients (configurable)
- ✅ **User Management**: Create/modify users (except Super Admins)
- ✅ **Assignment Management**: Create/modify client assignments
- ❌ **Limitations**: Cannot access Super Admin operations

### Requester
- ✅ **Assigned Clients Only**: Can only see assigned clients
- ✅ **Permission Requests**: Can create permission requests for assigned clients
- ✅ **Self Management**: Update own profile, view own assignments
- ❌ **Limitations**: Cannot see unassigned clients or other users' data

### Viewer
- ✅ **Read-Only Access**: View assigned clients and permissions
- ✅ **Self Management**: Update own profile, view own assignments
- ❌ **Limitations**: Cannot create permission requests or modify data

## Implementation Examples

### 1. Check User Access to Client

```python
from src.services.client_assignment_service import ClientAssignmentService

async def check_access(user_id: int, client_id: int, user_role: UserRole, db: AsyncSession):
    service = ClientAssignmentService(db)
    has_access = await service.check_user_client_access(
        user_id=user_id,
        client_id=client_id,
        user_role=user_role
    )
    return has_access
```

### 2. Get User's Accessible Clients

```python
async def get_accessible_clients(user_id: int, user_role: UserRole, db: AsyncSession):
    service = ClientAssignmentService(db)
    client_ids = await service.get_user_accessible_clients(
        user_id=user_id,
        user_role=user_role
    )
    return client_ids
```

### 3. Create Bulk Assignments

```python
from src.models.schemas import ClientAssignmentBulkCreate

async def bulk_assign_users(db: AsyncSession, assigned_by_id: int):
    bulk_data = ClientAssignmentBulkCreate(
        user_ids=[3, 4, 5],
        client_ids=[1, 2],
        notes="Quarterly project assignments"
    )
    
    service = ClientAssignmentService(db)
    assignments = await service.bulk_create_assignments(bulk_data, assigned_by_id)
    return assignments
```

### 4. Using Access Control Decorators

```python
from src.core.auth_dependencies import require_permissions, require_client_access

@router.get("/clients/{client_id}/sensitive-data")
@require_permissions(["read_client"])
async def get_sensitive_data(
    client_id: int,
    current_user: User = Depends(require_client_access),  # Validates client access
    db: AsyncSession = Depends(get_db)
):
    # User is guaranteed to have access to this client
    return {"data": "sensitive information"}
```

## Security Considerations

### Data Isolation
- **Client Boundaries**: Strict separation between client data
- **Role Boundaries**: Users cannot escalate privileges
- **Assignment Boundaries**: Users cannot access unassigned clients

### Audit Logging
- **All Changes Tracked**: Client assignments, modifications, deletions
- **Actor Attribution**: Who performed what action when
- **Detailed Context**: Full details of assignment changes

### Performance Optimization
- **Efficient Queries**: Proper indexing on assignment tables
- **Caching Strategy**: Cache user accessible clients
- **Bulk Operations**: Minimize database round trips

## Migration and Deployment

### Database Migration
1. Run Alembic migration: `alembic upgrade head`
2. The migration creates the `client_assignments` table and indexes
3. Existing data remains intact

### Backward Compatibility
- **API Compatibility**: Original endpoints continue to work
- **Enhanced Endpoints**: New endpoints provide additional functionality
- **Gradual Migration**: Can migrate users to assignment system gradually

### Demo Data
Run the enhanced server with demo data:
```bash
python start_enhanced_server.py
```

This creates:
- 5 demo users with different roles
- 3 demo clients
- Multiple client assignments demonstrating the system

## Best Practices

### Assignment Management
1. **Regular Audits**: Review client assignments quarterly
2. **Expiration Dates**: Set appropriate expiration dates for temporary access
3. **Bulk Operations**: Use bulk endpoints for efficiency
4. **Status Management**: Use inactive status instead of deletion for audit trails

### Access Control
1. **Principle of Least Privilege**: Assign minimal necessary access
2. **Regular Reviews**: Audit user access rights periodically
3. **Automated Validation**: Use access control decorators consistently
4. **Clear Documentation**: Document access requirements for each endpoint

### Performance
1. **Index Utilization**: Ensure proper database indexes are in place
2. **Query Optimization**: Use selective queries with appropriate filtering
3. **Caching Strategy**: Cache frequently accessed data like user permissions
4. **Bulk Operations**: Prefer bulk operations for multiple assignments

## Troubleshooting

### Common Issues

#### User Cannot Access Client
1. Check if user has active assignment to client
2. Verify user role has appropriate permissions
3. Check assignment expiration date
4. Review assignment status (active/inactive/suspended)

#### Permission Denied Errors
1. Verify user authentication token
2. Check user role and permissions
3. Confirm client assignment exists and is active
4. Review audit logs for access attempts

#### Performance Issues
1. Check database indexes are present
2. Review query patterns for N+1 issues
3. Monitor cache hit rates
4. Analyze slow query logs

### Debugging Tools

#### Access Control Summary
```http
GET /api/client-assignments/access-control/{user_id}
```
Returns comprehensive access information for a user.

#### Validate Access
```http
POST /api/client-assignments/validate-access/{client_id}
```
Tests whether current user can access a specific client.

#### System Statistics
```http
GET /api/system/stats
```
Returns system-wide statistics including assignment counts.

## Future Enhancements

### Planned Features
1. **Temporary Access**: Time-limited client access with automatic expiration
2. **Access Requests**: Users can request access to additional clients
3. **Client Groups**: Hierarchical client organization
4. **Advanced Permissions**: Fine-grained permissions within clients
5. **Client Delegation**: Allow clients to manage their own user assignments

### Integration Opportunities
1. **External Identity Providers**: SAML/OAuth integration
2. **Automated Provisioning**: Integration with HR systems
3. **Advanced Analytics**: Access pattern analysis and optimization
4. **Mobile Applications**: Native mobile app support
5. **Third-party Integrations**: CRM and project management tools

---

This comprehensive client assignment and access control system provides enterprise-grade security and flexibility while maintaining ease of use and strong performance characteristics.