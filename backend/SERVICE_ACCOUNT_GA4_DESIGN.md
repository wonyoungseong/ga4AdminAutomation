# Service Account and GA4 Property Relationship Management Design

## Business Logic Overview

### Core Purpose
The GA4 Admin Automation system manages Google Analytics 4 property access through a structured permission management system that uses Google Service Accounts as the technical bridge between users and GA4 properties.

### Key Business Entities

#### 1. Service Accounts
**Purpose**: 
- Technical authentication mechanism for Google API access
- Client-specific isolation for security and audit purposes
- Bridge between internal users and external GA4 properties

**Business Rules**:
- Each Client can have multiple Service Accounts
- Service Accounts are tied to specific Google Cloud Projects
- Service Accounts must have appropriate GA4 Admin API permissions
- Service Accounts can manage multiple GA4 Properties

#### 2. GA4 Properties
**Purpose**:
- Represent Google Analytics 4 properties (websites, mobile apps, etc.)
- Target resources for permission grants
- Scope of access control

**Business Rules**:
- Properties are identified by GA4 Property IDs
- Properties belong to GA4 Accounts (managed by Service Accounts)
- Properties can have different permission levels for different users

#### 3. Permission Grants
**Purpose**:
- Central workflow entity managing access requests
- Links Users, Clients, Service Accounts, and GA4 Properties
- Provides audit trail and lifecycle management

**Business Rules**:
- Users can only request access to properties of clients they're assigned to
- Different permission levels require different approval authorities
- Permissions can expire and be extended
- All permission changes are audited

## Technical Implementation

### Enhanced Database Schema

```sql
-- Service Account Properties Table (New)
CREATE TABLE service_account_properties (
    id SERIAL PRIMARY KEY,
    service_account_id INTEGER NOT NULL REFERENCES service_accounts(id),
    ga_property_id VARCHAR(50) NOT NULL,
    property_name VARCHAR(255),
    property_account_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated_at TIMESTAMP WITH TIME ZONE,
    validation_status VARCHAR(20) DEFAULT 'unknown', -- 'valid', 'invalid', 'unknown'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(service_account_id, ga_property_id)
);

-- Property Access Bindings Cache (New)
CREATE TABLE property_access_bindings (
    id SERIAL PRIMARY KEY,
    service_account_id INTEGER NOT NULL REFERENCES service_accounts(id),
    ga_property_id VARCHAR(50) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    roles TEXT[], -- Array of GA4 roles
    binding_name VARCHAR(500), -- Google's binding resource name
    is_active BOOLEAN DEFAULT TRUE,
    synchronized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(service_account_id, ga_property_id, user_email)
);

-- Enhanced Service Accounts
ALTER TABLE service_accounts ADD COLUMN IF NOT EXISTS project_id VARCHAR(255);
ALTER TABLE service_accounts ADD COLUMN IF NOT EXISTS key_version INTEGER DEFAULT 1;
ALTER TABLE service_accounts ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE service_accounts ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'unknown';
ALTER TABLE service_accounts ADD COLUMN IF NOT EXISTS health_checked_at TIMESTAMP WITH TIME ZONE;

-- Enhanced Permission Grants (additional fields)
ALTER TABLE permission_grants ADD COLUMN IF NOT EXISTS binding_name VARCHAR(500);
ALTER TABLE permission_grants ADD COLUMN IF NOT EXISTS synchronized_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE permission_grants ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending';
```

### API Endpoints Design

#### Service Account Management
```python
# POST /api/service-accounts
# GET /api/service-accounts
# GET /api/service-accounts/{id}
# PUT /api/service-accounts/{id}
# DELETE /api/service-accounts/{id}

# Service Account Properties
# GET /api/service-accounts/{id}/properties
# POST /api/service-accounts/{id}/properties/discover
# PUT /api/service-accounts/{id}/properties/{property_id}

# Service Account Health
# GET /api/service-accounts/{id}/health
# POST /api/service-accounts/{id}/health/check
```

#### GA4 Integration Endpoints
```python
# Property Discovery
# GET /api/ga4/accounts
# GET /api/ga4/properties
# GET /api/ga4/properties/{property_id}

# Permission Management
# GET /api/ga4/properties/{property_id}/permissions
# POST /api/ga4/properties/{property_id}/permissions
# DELETE /api/ga4/properties/{property_id}/permissions/{binding_name}

# Synchronization
# POST /api/ga4/sync/permissions
# GET /api/ga4/sync/status
```

### Business Logic Services

#### ServiceAccountService
**Responsibilities**:
- Manage service account lifecycle
- Validate service account credentials
- Discover available GA4 properties
- Health check service accounts

**Key Methods**:
```python
async def create_service_account(client_id: int, sa_data: ServiceAccountCreate)
async def validate_service_account(sa_id: int) -> bool
async def discover_properties(sa_id: int) -> List[GA4Property]
async def health_check(sa_id: int) -> HealthStatus
async def rotate_credentials(sa_id: int) -> ServiceAccount
```

#### GA4IntegrationService
**Responsibilities**:
- Interface with Google Analytics Admin API
- Manage property access bindings
- Synchronize permissions between system and GA4
- Handle GA4 API errors and retries

**Key Methods**:
```python
async def grant_property_access(property_id: str, email: str, roles: List[str])
async def revoke_property_access(property_id: str, email: str)
async def list_property_bindings(property_id: str)
async def sync_permissions(force: bool = False)
```

#### PermissionWorkflowService
**Responsibilities**:
- Orchestrate permission request workflows
- Apply business rules for approvals
- Manage permission lifecycle
- Send notifications

**Key Methods**:
```python
async def submit_permission_request(user_id: int, request: PermissionGrantCreate)
async def approve_permission(grant_id: int, approver_id: int)
async def process_auto_approvals()
async def expire_permissions()
```

## Security and Access Control

### Service Account Security
1. **Credential Management**: Service account keys stored in Google Secret Manager
2. **Principle of Least Privilege**: Service accounts have minimal required permissions
3. **Key Rotation**: Regular rotation of service account keys
4. **Access Logging**: All service account usage is logged and monitored

### Permission Hierarchy
```
Super Admin → Can manage all service accounts and approve all permissions
Admin → Can manage client service accounts and approve most permissions
Requester → Can request permissions for assigned clients only
Viewer → Can view assigned client permissions only
```

### Client Access Control
1. **Assignment-Based Access**: Users can only work with clients they're assigned to
2. **Service Account Isolation**: Each client's service accounts are isolated
3. **Property Scoping**: Users can only request access to properties their client owns

## Workflow Examples

### 1. New Client Onboarding
```
1. Admin creates Client record
2. Admin creates ServiceAccount for client (with Google credentials)
3. System discovers available GA4 properties for the service account
4. Admin assigns users to the client
5. Users can now request permissions for the client's properties
```

### 2. Permission Request Flow
```
1. User (Requester) submits permission request for specific GA4 property
2. System validates:
   - User is assigned to the client
   - Property exists and is accessible via service account
   - No duplicate active requests
3. Request enters approval workflow based on permission level
4. Upon approval:
   - System uses service account to grant GA4 access
   - Permission grant is marked as approved
   - User receives notification
5. System periodically syncs to ensure GA4 state matches internal records
```

### 3. Permission Lifecycle Management
```
- Auto-expiration for viewer/analyst permissions (30 days default)
- Manual expiration for editor/admin permissions
- Extension workflow for renewed access
- Revocation workflow for immediate access removal
- Bulk operations for client offboarding
```

## Monitoring and Maintenance

### Health Monitoring
1. **Service Account Health**: Regular validation of service account credentials
2. **GA4 API Health**: Monitor API quotas and error rates
3. **Permission Sync**: Detect and alert on synchronization issues
4. **Access Validation**: Periodic validation of actual vs. recorded permissions

### Audit and Compliance
1. **Complete Audit Trail**: All permission changes are logged with actor, timestamp, and reason
2. **Access Reviews**: Regular reports of who has access to what
3. **Compliance Reports**: Support for SOX, GDPR, and other compliance requirements
4. **Data Retention**: Configurable retention policies for audit logs

## Migration Strategy

### Phase 1: Foundation
- Enhance database schema
- Implement core service account management
- Basic GA4 integration

### Phase 2: Workflow Integration
- Permission request workflows
- Approval processes
- Notification system

### Phase 3: Advanced Features
- Automated synchronization
- Health monitoring
- Advanced reporting

### Phase 4: Optimization
- Performance optimization
- Advanced security features
- Analytics and insights

## Performance Considerations

### Scalability
- Database indexing for efficient queries
- Caching of GA4 API responses
- Batch processing for bulk operations
- Async processing for long-running tasks

### Reliability
- Circuit breakers for GA4 API calls
- Retry logic with exponential backoff
- Graceful degradation when GA4 API is unavailable
- Transaction management for data consistency

## API Rate Limiting and Quotas

### Google Analytics Admin API Limits
- 25,000 requests per day per project
- 5 requests per second per user
- Implement intelligent rate limiting and queuing

### Internal Rate Limiting
- User-based rate limits for API endpoints
- Client-based rate limits for bulk operations
- Admin override capabilities for emergency operations