# GA4 Admin Automation - QA Testing Areas and Common Error Patterns

## 🔍 Critical QA Testing Areas

### 1. Authentication & Session Management
**Priority: Critical**
- JWT token validation and refresh mechanism
- Cross-tab session synchronization
- Token expiry handling
- Login state persistence across page refreshes
- Logout functionality across all tabs

**Common Errors:**
- SSL protocol errors with HTTP/HTTPS mismatch
- Token expiry not properly checked before API calls
- Session lost on page refresh
- Cross-tab synchronization failures
- Unauthorized redirects to login page

### 2. Role-Based Access Control (RBAC)
**Priority: Critical**
- Role permission enforcement
- UI element visibility based on roles
- API endpoint access control
- Role transition handling (Admin → Requester)

**Common Errors:**
- Permission elevation vulnerabilities
- UI showing unauthorized features
- API endpoints accessible without proper roles
- Role changes not immediately reflected

### 3. GA4 API Integration
**Priority: High**
- Service account authentication
- Property access validation
- User permission grant/revoke operations
- API rate limiting handling
- Bulk operations performance

**Common Errors:**
- Service account credential failures
- GA4 API quota exceeded
- Timeout on bulk operations
- Stale permission data
- Async operation status tracking

### 4. Database Operations
**Priority: High**
- Transaction integrity
- Connection pooling
- Migration consistency
- Data validation
- Concurrent access handling

**Common Errors:**
- Connection pool exhaustion
- Transaction deadlocks
- Migration failures between SQLite → PostgreSQL
- Foreign key constraint violations
- Race conditions in concurrent updates

### 5. Frontend State Management
**Priority: Medium**
- API response caching
- Loading states
- Error boundary handling
- Form validation
- Real-time updates

**Common Errors:**
- Stale data display
- Loading spinners stuck
- Unhandled promise rejections
- Form submission without validation
- Memory leaks from event listeners

### 6. Email Notification System
**Priority: Medium**
- SMTP connection reliability
- Email template rendering
- Notification scheduling
- Bulk email handling
- Bounce/failure handling

**Common Errors:**
- SMTP authentication failures
- Email template variables missing
- Notification queue overflow
- Rate limiting by email providers
- Missing error notifications

## 🐛 Common Error Patterns & Solutions

### Pattern 1: Authentication Token Issues
```javascript
// Problem: Token expired but not refreshed
// Symptom: 401 errors, redirect to login

// Solution: Implement token refresh interceptor
const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  // Update tokens
};
```

### Pattern 2: CORS and SSL Issues
```yaml
# Problem: Mixed content (HTTP/HTTPS)
# Symptom: ERR_SSL_PROTOCOL_ERROR

# Solution: Remove upgrade-insecure-requests from CSP
# Ensure all API calls use consistent protocol
NEXT_PUBLIC_API_URL: "http://localhost:8000"  # Development
NEXT_PUBLIC_API_URL: "https://api.domain.com"  # Production
```

### Pattern 3: Database Connection Failures
```python
# Problem: Connection pool exhaustion
# Symptom: TimeoutError, connection refused

# Solution: Implement connection retry logic
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_db_connection():
    return await database.connect()
```

### Pattern 4: React State Update Warnings
```typescript
// Problem: State updates on unmounted components
// Symptom: Memory leaks, console warnings

// Solution: Cleanup in useEffect
useEffect(() => {
  let mounted = true;
  
  fetchData().then(data => {
    if (mounted) setState(data);
  });
  
  return () => { mounted = false; };
}, []);
```

### Pattern 5: GA4 API Rate Limiting
```python
# Problem: 429 Too Many Requests
# Symptom: API calls failing intermittently

# Solution: Implement exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(RateLimitError)
)
async def call_ga4_api():
    # API call logic
```

## 🧪 QA Test Scenarios

### Scenario 1: Multi-Tab Session Test
1. Login in Tab 1
2. Open Tab 2, navigate to dashboard
3. Logout in Tab 1
4. Verify Tab 2 redirects to login
5. Check no orphaned sessions

### Scenario 2: Permission Escalation Test
1. Login as Requester
2. Attempt to access Admin endpoints
3. Verify 403 Forbidden responses
4. Check audit logs for attempts

### Scenario 3: Bulk Operation Stress Test
1. Create 100+ permission requests
2. Bulk approve/reject operations
3. Monitor response times
4. Check database integrity
5. Verify email queue processing

### Scenario 4: Network Failure Recovery
1. Start long-running operation
2. Disconnect network
3. Reconnect after timeout
4. Verify graceful error handling
5. Check operation can be retried

### Scenario 5: Concurrent User Test
1. Multiple users modify same resource
2. Verify optimistic locking works
3. Check conflict resolution
4. Validate audit trail accuracy

## 🔧 QA Automation Tools

### Backend Testing
```bash
# Unit tests
pytest tests/unit/ -v --cov=src

# Integration tests
pytest tests/integration/ --db=test

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Frontend Testing
```bash
# Component tests
npm run test

# E2E tests
npx playwright test

# Accessibility tests
npm run test:a11y
```

### API Testing
```bash
# OpenAPI validation
python -m openapi_spec_validator http://localhost:8000/api/openapi.json

# Contract testing
npm run test:contract
```

## 📊 QA Metrics to Track

1. **Test Coverage**
   - Backend: >80% unit, >70% integration
   - Frontend: >75% component, >60% E2E

2. **Performance Benchmarks**
   - API response time: <200ms (p95)
   - Page load time: <3s (3G network)
   - Database query time: <100ms

3. **Error Rates**
   - API error rate: <0.1%
   - Frontend crash rate: <0.01%
   - Failed deployments: <5%

4. **Security Metrics**
   - Failed auth attempts tracked
   - SQL injection tests: 100% pass
   - XSS prevention: 100% coverage

## 🚨 Critical Issues Checklist

- [ ] Authentication bypass vulnerabilities
- [ ] Data exposure through API
- [ ] SQL injection points
- [ ] XSS vulnerabilities
- [ ] CSRF token validation
- [ ] Rate limiting bypass
- [ ] Session fixation
- [ ] Privilege escalation
- [ ] Sensitive data in logs
- [ ] Unencrypted data transmission