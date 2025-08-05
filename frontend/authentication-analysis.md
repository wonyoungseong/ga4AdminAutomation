# Authentication State Management Analysis

## Code Review Findings

### Current Authentication Flow

#### 1. Authentication Context (`auth-context.tsx`)
**Key Components:**
- Uses `useClientOnly` hook to ensure client-side execution
- Stores JWT token in localStorage as 'auth_token'
- Fetches user info on component mount if token exists
- Has login/logout functionality

**Potential Issues:**
```typescript
useEffect(() => {
  if (!isClient) {
    setIsLoading(false);  // ⚠️ Sets loading to false on server-side
    return;
  }
  
  const storedToken = localStorage.getItem('auth_token');
  if (storedToken) {
    setToken(storedToken);
    fetchUserInfo(storedToken);  // ⚠️ Async call but no error handling for token expiry
  } else {
    setIsLoading(false);
  }
}, [isClient]);
```

#### 2. Dashboard Layout (`dashboard/layout.tsx`)
**Protection Logic:**
```typescript
useEffect(() => {
  if (!isLoading && !user) {
    // Store the intended destination before redirecting to login
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('redirectAfterLogin', pathname);
    }
    router.push("/login");
  }
}, [user, isLoading, router, pathname]);
```

**Issues Identified:**
- Redirects to login immediately when `!user` and `!isLoading`
- No grace period for token refresh attempts
- Runs on every route change, potentially causing multiple redirects

#### 3. API Client (`api-client.ts`)
**Token Management:**
- Automatic token refresh on 401 responses
- Stores both access and refresh tokens
- Has comprehensive error handling

**Critical Issue:**
```typescript
if (response.status === 401) {
  // Try to refresh token first
  const refreshedToken = await this.sessionManager.refreshToken();
  if (refreshedToken) {
    // Retry the request with new token
    // ... retry logic
  }
  
  // If refresh failed, clear session and redirect
  this.sessionManager.removeToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';  // ⚠️ Hard redirect bypasses React Router
  }
}
```

## Root Cause Analysis

### Primary Issue: Race Condition in Authentication State
1. **Initial Load**: Auth context loads, `isLoading = true`
2. **Token Check**: Finds token in localStorage, calls `fetchUserInfo()`
3. **API Call**: If token is expired, API returns 401
4. **Token Refresh**: API client attempts token refresh
5. **Race Condition**: Dashboard layout checks auth state before refresh completes
6. **Premature Redirect**: Layout redirects to login while refresh is still in progress

### Secondary Issues

#### 1. Inconsistent Redirect Methods
- Auth context uses `router.push('/login')`
- API client uses `window.location.href = '/login'`
- This can cause navigation conflicts

#### 2. No Coordination Between Components
- API client handles token refresh independently
- Auth context doesn't know about ongoing refresh attempts
- Dashboard layout doesn't wait for refresh completion

#### 3. Multiple Redirect Triggers
- Dashboard layout effect runs on every route change
- Can trigger multiple simultaneous redirects
- No debouncing or single-redirect protection

## Test Execution Plan (Manual Testing Required)

### Phase 1: Basic Functionality
1. **Fresh Login Test**
   ```
   1. Clear all localStorage/sessionStorage
   2. Navigate to http://localhost:3000
   3. Should redirect to /login
   4. Login with admin@test.com / admin123
   5. Should redirect to /dashboard
   ✅ Expected: Successful login and dashboard load
   ```

2. **Dashboard Navigation Test**
   ```
   1. From dashboard, navigate to each section:
      - /dashboard/users
      - /dashboard/permissions  
      - /dashboard/service-accounts
      - /dashboard/ga4-properties
      - /dashboard/audit
   ✅ Expected: All pages load without login redirect
   ```

### Phase 2: Session Persistence
3. **Page Refresh Test**
   ```
   1. Login and navigate to any dashboard page
   2. Press F5 or Ctrl+R to refresh
   3. Monitor network tab for API calls
   ❌ Expected Issue: Possible redirect to login during token refresh
   ```

4. **New Tab Test**
   ```
   1. Login in Tab 1
   2. Open Tab 2, navigate to http://localhost:3000/dashboard
   ❌ Expected Issue: Tab 2 may redirect to login due to race condition
   ```

### Phase 3: Edge Cases
5. **Token Expiry Simulation**
   ```
   1. Login successfully
   2. Manually edit localStorage 'auth_token' to invalid value
   3. Navigate to dashboard page
   4. Monitor console for errors
   ❌ Expected Issue: Multiple redirect attempts, console errors
   ```

6. **Network Error Test**
   ```
   1. Login successfully
   2. Disconnect network/block API calls
   3. Navigate between dashboard pages
   ❌ Expected Issue: Timeout errors, unexpected redirects
   ```

## Expected Test Results

### Successful Scenarios
- ✅ Fresh login with valid credentials
- ✅ Logout functionality
- ✅ Basic dashboard navigation (when session is stable)

### Problematic Scenarios
- ❌ Page refresh (race condition with token refresh)
- ❌ New tab navigation (localStorage sync timing)
- ❌ Rapid navigation between pages (multiple redirect triggers)
- ❌ Network interruptions (error handling gaps)

## Recommended Fixes

### 1. Coordinate Token Refresh with Auth Context
```typescript
// Add to auth context
const [isRefreshing, setIsRefreshing] = useState(false);

const refreshToken = async () => {
  if (isRefreshing) return false;
  setIsRefreshing(true);
  try {
    const newToken = await typeSafeApiClient.refreshAuthToken();
    if (newToken) {
      setToken(newToken);
      await fetchUserInfo(newToken);
      return true;
    }
  } finally {
    setIsRefreshing(false);
  }
  return false;
};
```

### 2. Update Dashboard Layout Protection
```typescript
useEffect(() => {
  if (!isLoading && !user && !isRefreshing) {
    // Add delay to allow token refresh
    const timer = setTimeout(() => {
      if (!user && !isRefreshing) {
        sessionStorage.setItem('redirectAfterLogin', pathname);
        router.push("/login");
      }
    }, 1000);
    
    return () => clearTimeout(timer);
  }
}, [user, isLoading, isRefreshing, router, pathname]);
```

### 3. Consistent Redirect Handling
```typescript
// Replace window.location.href with router.push in API client
// Or use a centralized auth service for redirects
```

## Console Monitoring Commands

For manual testing, monitor these in browser console:

```javascript
// Check authentication state
console.log('Auth Token:', localStorage.getItem('auth_token'));
console.log('User State:', /* auth context user state */);

// Monitor API calls
// Watch Network tab for:
// - POST /api/auth/login
// - GET /api/auth/me  
// - POST /api/auth/refresh
// - Any 401 responses

// Monitor redirects
window.addEventListener('beforeunload', (e) => {
  console.log('Page unloading:', window.location.href);
});
```