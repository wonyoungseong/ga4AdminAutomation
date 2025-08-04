# Client Assignment System Integration Guide

This guide provides practical steps to integrate the newly tested client assignment system with the existing GA4 Admin Automation backend.

## Integration Overview

The client assignment system has been thoroughly tested and is ready for integration. The enhanced system adds:

- User-client assignment management
- Role-based client access control  
- Bulk assignment operations
- Comprehensive audit logging
- API endpoints for assignment management

## Step-by-Step Integration

### 1. Database Setup

#### Update Database Models
The enhanced database models are already defined in `/src/models/db_models.py`:

```python
# Key models added:
- ClientAssignment: User-client relationship with metadata
- ClientAssignmentStatus: Status enumeration (active/inactive/suspended)
- Enhanced User model with client_assignments relationship
- Enhanced Client model with client_assignments relationship
```

#### Run Database Migration
```bash
# Apply the client assignment migration
alembic upgrade head

# Or run the specific migration:
alembic upgrade +1  # If 003_add_client_assignments.py is next
```

### 2. Service Integration

#### Add ClientAssignmentService to Dependency Injection
Update `/src/core/dependencies.py`:

```python
from ..services.client_assignment_service import ClientAssignmentService

def get_client_assignment_service(
    db: AsyncSession = Depends(get_db)
) -> ClientAssignmentService:
    return ClientAssignmentService(db)
```

#### Update Main Application
In `/src/main.py` or your main application file:

```python
from .api.routers import client_assignments

# Add the router
app.include_router(
    client_assignments.router,
    prefix="/api",
    tags=["Client Assignments"]
)
```

### 3. API Endpoint Integration

#### Copy Enhanced Routers
The client assignment API router is already implemented in:
- `/src/api/routers/client_assignments.py`

#### Update Authentication Dependencies
Ensure `/src/core/auth_dependencies.py` includes:

```python
async def get_user_accessible_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[int]:
    """Get list of client IDs accessible to current user"""
    service = ClientAssignmentService(db)
    return await service.get_user_accessible_clients(
        current_user.id, 
        current_user.role
    )
```

### 4. Update Existing Endpoints

#### Modify Client Endpoints
Update existing client endpoints to respect user assignments:

```python
# In client router
@router.get("/clients")
async def get_clients(
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    # ... other parameters
):
    # Filter clients based on user access
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        clients = [c for c in clients if c.id in accessible_clients]
    return clients
```

#### Modify Permission Endpoints
Update permission endpoints to include client context:

```python
# In permission router
@router.get("/permissions")
async def get_permissions(
    accessible_clients: List[int] = Depends(get_user_accessible_clients),
    # ... other parameters
):
    # Filter permissions based on accessible clients
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        permissions = [p for p in permissions 
                      if get_client_id_for_permission(p) in accessible_clients]
    return permissions
```

### 5. Configuration Updates

#### Update RBAC Permissions
Add new permissions to `/src/core/config.py` or where ROLE_PERMISSIONS is defined:

```python
ROLE_PERMISSIONS = {
    "Super Admin": [
        # ... existing permissions
        "manage_client_assignments",
        "view_all_assignments",
        "bulk_assign_clients"
    ],
    "Admin": [
        # ... existing permissions  
        "manage_client_assignments",
        "view_managed_assignments"
    ],
    "Requester": [
        # ... existing permissions
        "view_own_assignments"
    ],
    "Viewer": [
        # ... existing permissions
        "view_own_assignments"
    ]
}
```

### 6. Environment Configuration

#### Update Environment Variables
Add any new configuration to `.env`:

```bash
# Client Assignment Settings
CLIENT_ASSIGNMENT_AUTO_EXPIRE_DAYS=365
CLIENT_ASSIGNMENT_BULK_LIMIT=100
CLIENT_ASSIGNMENT_AUDIT_RETENTION_DAYS=2555  # 7 years
```

### 7. Testing Integration

#### Run Integration Tests
```bash
# Run service tests
python test_client_assignment_system.py

# Run API tests (with enhanced server)
python test_client_assignment_api.py

# Run existing tests to ensure no regression
python -m pytest tests/
```

#### Verify Database Schema
```bash
# Check that migrations applied correctly
alembic current
alembic history

# Verify tables created
python -c "
from src.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
"
```

### 8. Deployment Checklist

#### Pre-Deployment
- [ ] Database migration tested in staging
- [ ] All tests passing
- [ ] API documentation updated
- [ ] Environment variables configured
- [ ] Backup procedures updated

#### Deployment Steps
1. **Backup Database**
   ```bash
   # Create backup before migration
   pg_dump ga4_admin > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Deploy Code**
   ```bash
   # Deploy application code
   git pull origin main
   pip install -r requirements.txt
   ```

3. **Run Migrations**
   ```bash
   # Apply database changes
   alembic upgrade head
   ```

4. **Restart Services**
   ```bash
   # Restart application server
   systemctl restart ga4-admin-backend
   ```

5. **Verify Deployment**
   ```bash
   # Test key endpoints
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/api/client-assignments/my/accessible-clients
   ```

#### Post-Deployment
- [ ] Monitor application logs
- [ ] Verify API endpoints responding
- [ ] Check database performance
- [ ] Test user assignment workflows
- [ ] Monitor audit log generation

### 9. Rollback Procedures

#### Code Rollback
```bash
# Rollback to previous version
git checkout <previous-commit>
pip install -r requirements.txt
systemctl restart ga4-admin-backend
```

#### Database Rollback
```bash
# Rollback database migration if needed
alembic downgrade -1

# Restore from backup if necessary
psql ga4_admin < backup_20250804_053525.sql
```

### 10. Monitoring and Maintenance

#### Key Metrics to Monitor
- Client assignment creation/update rates
- User access control failures
- API response times for assignment endpoints
- Database query performance
- Audit log growth rate

#### Regular Maintenance Tasks
- Review and cleanup expired assignments
- Monitor audit log storage growth
- Validate user access patterns
- Performance optimization of bulk operations
- Security review of access control rules

## Enhanced Features Available

### Client Assignment Management
- Create individual user-client assignments
- Bulk assign multiple users to multiple clients
- Update assignment status and metadata
- Delete assignments with audit trail

### Access Control Features
- Role-based client filtering
- Assignment-based access restrictions
- Configurable admin access patterns
- Inactive client/user handling

### API Endpoints Available
```
POST   /api/client-assignments              # Create assignment
GET    /api/client-assignments              # List assignments
GET    /api/client-assignments/{id}         # Get specific assignment
PUT    /api/client-assignments/{id}         # Update assignment
DELETE /api/client-assignments/{id}         # Delete assignment
POST   /api/client-assignments/bulk         # Bulk create assignments
GET    /api/client-assignments/users/{id}/clients  # Get user's clients
GET    /api/client-assignments/clients/{id}/users  # Get client's users
GET    /api/client-assignments/access-control/{id} # Get access summary
POST   /api/client-assignments/validate-access/{id} # Validate access
GET    /api/client-assignments/my/accessible-clients # Get accessible clients
```

### Audit Features
- All assignment operations logged
- Detailed change tracking
- Actor identification and IP tracking
- Integration with existing audit system

## Troubleshooting

### Common Issues

#### Migration Failures
```bash
# Check migration status
alembic current
alembic history

# Show pending migrations
alembic show

# Force migration (if safe)
alembic stamp head
```

#### Permission Errors
```bash
# Verify role permissions
python -c "
from src.core.config import ROLE_PERMISSIONS
print(ROLE_PERMISSIONS)
"

# Check user roles in database
python -c "
from src.core.database import get_db
from src.models.db_models import User
# Query user roles
"
```

#### API Integration Issues
```bash
# Test endpoints manually
curl -X GET http://localhost:8000/api/client-assignments \
     -H "Authorization: Bearer $TOKEN"

# Check API documentation
curl http://localhost:8000/docs
```

### Performance Issues
- Monitor database query performance
- Check for missing indexes on user_id, client_id
- Optimize bulk operations if needed
- Consider caching for frequently accessed data

### Security Concerns
- Verify access control logic in production
- Monitor failed access attempts
- Review audit logs regularly
- Validate user permissions after role changes

## Support and Documentation

### Additional Resources
- API Documentation: `/docs` endpoint
- Database Schema: `/src/models/db_models.py`
- Service Implementation: `/src/services/client_assignment_service.py`
- Test Suite: `test_client_assignment_system.py`
- Test Reports: `CLIENT_ASSIGNMENT_SYSTEM_TEST_REPORT.md`

### Contact Information
- System Architecture: backend-architect agent
- Test Coverage: Comprehensive test suite included
- Documentation: Auto-generated from code and tests

---

**Integration Status:** ✅ Ready for deployment with comprehensive testing completed.