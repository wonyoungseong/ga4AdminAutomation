# GA4 Admin Automation System - Frontend Specification

## Overview

The frontend of the GA4 Admin Automation System is built with Next.js 14 using the App Router, providing a modern, performant, and SEO-friendly web application. This specification details the complete frontend architecture, components, and implementation strategy.

## Architecture

### Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.x
- **UI Library**: Shadcn UI + Radix UI
- **Styling**: Tailwind CSS + CSS Modules
- **State Management**: Zustand + React Query
- **Forms**: React Hook Form + Zod
- **Icons**: Lucide React
- **Testing**: Vitest + React Testing Library + Playwright

### Directory Structure
```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Auth group
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── reset-password/
│   │   ├── (dashboard)/       # Dashboard group
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── users/
│   │   │   ├── permissions/
│   │   │   ├── clients/
│   │   │   ├── service-accounts/
│   │   │   ├── analytics/
│   │   │   └── audit/
│   │   ├── api/               # API routes
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/            # Reusable components
│   │   ├── ui/               # Shadcn UI components
│   │   ├── forms/
│   │   ├── tables/
│   │   ├── charts/
│   │   └── layouts/
│   ├── hooks/                # Custom hooks
│   ├── lib/                  # Utilities
│   ├── services/             # API services
│   ├── stores/               # Zustand stores
│   ├── types/                # TypeScript types
│   └── utils/                # Helper functions
├── public/                   # Static assets
├── tests/                    # Test files
└── package.json
```

## Component Architecture

### Core Components

#### 1. Layout Components
```typescript
// src/components/layouts/DashboardLayout.tsx
interface DashboardLayoutProps {
  children: React.ReactNode;
  user: User;
}

Components:
- Header (with user menu, notifications)
- Sidebar (navigation, collapsible)
- Main content area
- Footer
```

#### 2. Authentication Components
```typescript
// src/components/auth/
- LoginForm
- RegisterForm
- PasswordResetForm
- AuthGuard (HOC)
- SessionManager
```

#### 3. Data Display Components
```typescript
// src/components/tables/
- DataTable (generic, sortable, filterable)
- UserTable
- PermissionTable
- ClientTable
- AuditLogTable

// src/components/charts/
- AnalyticsChart
- PermissionStatusChart
- UserActivityChart
- SystemHealthChart
```

#### 4. Form Components
```typescript
// src/components/forms/
- UserForm
- PermissionRequestForm
- ClientForm
- ServiceAccountForm
- NotificationPreferencesForm
```

#### 5. UI Components (Shadcn)
```typescript
// src/components/ui/
- Button, Card, Dialog, Dropdown
- Input, Select, Checkbox, Radio
- Toast, Alert, Badge, Avatar
- Tabs, Accordion, Progress
- Command, Popover, Sheet
```

## State Management

### Zustand Stores

#### 1. Auth Store
```typescript
interface AuthStore {
  user: User | null;
  tokens: TokenPair | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}
```

#### 2. UI Store
```typescript
interface UIStore {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  notifications: Notification[];
  toggleTheme: () => void;
  toggleSidebar: () => void;
  addNotification: (notification: Notification) => void;
}
```

#### 3. Permission Store
```typescript
interface PermissionStore {
  permissions: Permission[];
  loading: boolean;
  filters: PermissionFilters;
  fetchPermissions: () => Promise<void>;
  updateFilters: (filters: Partial<PermissionFilters>) => void;
}
```

### React Query Configuration

```typescript
// src/lib/query-client.ts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});
```

## Routing Structure

### Public Routes
```
/                     # Landing page
/login               # Login page
/register            # Registration page
/reset-password      # Password reset
/verify-email        # Email verification
```

### Protected Routes
```
/dashboard           # Main dashboard
/dashboard/users     # User management
/dashboard/users/[id] # User details
/dashboard/permissions # Permission management
/dashboard/permissions/[id] # Permission details
/dashboard/clients   # Client management
/dashboard/clients/[id] # Client details
/dashboard/service-accounts # Service accounts
/dashboard/analytics # Analytics dashboard
/dashboard/audit     # Audit logs
/dashboard/settings  # User settings
/dashboard/settings/profile # Profile settings
/dashboard/settings/security # Security settings
/dashboard/settings/notifications # Notification preferences
```

## Implementation Phases

### Phase 1: Foundation Setup (Week 1)
**Time Estimate**: 40 hours
**Agent**: Frontend Agent 1 & 2

#### Tasks:
1. **Project Initialization** (Day 1)
   - Setup Next.js 14 with TypeScript
   - Configure Tailwind CSS
   - Install and setup Shadcn UI
   - Configure ESLint and Prettier
   - **Git Commit**: Every 30 minutes

2. **Base Layout Components** (Day 2-3)
   - Create layout structure
   - Implement responsive navigation
   - Setup dark theme support
   - Create loading states
   - **Git Commit**: Every 30 minutes

3. **Authentication UI** (Day 4-5)
   - Login/Register forms
   - Password reset flow
   - Auth context setup
   - Protected route wrapper
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ Project builds without errors
- ✓ All routes accessible
- ✓ Authentication flow complete
- ✓ Responsive design working

**QA Checkpoints**:
- [ ] Mobile responsiveness verified
- [ ] Dark theme consistency
- [ ] Form validation working
- [ ] Navigation smooth

### Phase 2: Core Features UI (Week 2)
**Time Estimate**: 40 hours
**Agent**: Frontend Agent 3 & 4

#### Tasks:
1. **User Management UI** (Day 6-7)
   - User list with DataTable
   - User creation/edit forms
   - Role assignment UI
   - Bulk actions support
   - **Git Commit**: Every 30 minutes

2. **Permission Management UI** (Day 8-9)
   - Permission request form
   - Permission list view
   - Approval/rejection interface
   - Status tracking UI
   - **Git Commit**: Every 30 minutes

3. **Dashboard Components** (Day 10)
   - Metrics cards
   - Recent activity feed
   - Quick actions panel
   - Status indicators
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ All CRUD operations functional
- ✓ Forms validate properly
- ✓ Tables sort and filter
- ✓ Dashboard renders data

**QA Checkpoints**:
- [ ] Form submissions work
- [ ] Table interactions smooth
- [ ] Error states handled
- [ ] Loading states shown

### Phase 3: Advanced Features (Week 3)
**Time Estimate**: 40 hours
**Agent**: Frontend Agent 1 & 3

#### Tasks:
1. **Analytics Dashboard** (Day 11-12)
   - Chart components setup
   - Real-time data updates
   - Export functionality
   - Custom date ranges
   - **Git Commit**: Every 30 minutes

2. **Notification System** (Day 13)
   - Toast notifications
   - Notification center
   - Read/unread states
   - Notification preferences
   - **Git Commit**: Every 30 minutes

3. **Audit Log Interface** (Day 14)
   - Activity timeline
   - Filterable log view
   - Export capabilities
   - Detail modals
   - **Git Commit**: Every 30 minutes

4. **Search & Filters** (Day 15)
   - Global search component
   - Advanced filters
   - Saved filter sets
   - Search highlighting
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ Charts render correctly
- ✓ Notifications appear/dismiss
- ✓ Audit logs searchable
- ✓ Filters work across views

**QA Checkpoints**:
- [ ] Chart performance acceptable
- [ ] Notifications don't overlap
- [ ] Search returns relevant results
- [ ] Filter state persists

### Phase 4: Integration & Polish (Week 4)
**Time Estimate**: 40 hours
**Agent**: Frontend Agent 2 & 4

#### Tasks:
1. **API Integration** (Day 16-17)
   - Setup API client
   - Implement interceptors
   - Error handling
   - Retry logic
   - **Git Commit**: Every 30 minutes

2. **State Management** (Day 18)
   - Zustand store setup
   - React Query integration
   - Optimistic updates
   - Cache management
   - **Git Commit**: Every 30 minutes

3. **Performance Optimization** (Day 19)
   - Code splitting
   - Lazy loading
   - Image optimization
   - Bundle analysis
   - **Git Commit**: Every 30 minutes

4. **Accessibility** (Day 20)
   - ARIA labels
   - Keyboard navigation
   - Screen reader support
   - Focus management
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ API calls efficient
- ✓ State synchronized
- ✓ Performance targets met
- ✓ Accessibility standards met

**QA Checkpoints**:
- [ ] No unnecessary re-renders
- [ ] API errors handled gracefully
- [ ] Page load <3s
- [ ] WCAG 2.1 AA compliant

### Phase 5: Testing & Documentation (Week 5)
**Time Estimate**: 40 hours
**Agent**: Frontend Agent 1-4 (collaborative)

#### Tasks:
1. **Unit Testing** (Day 21-22)
   - Component tests
   - Hook tests
   - Utility tests
   - Store tests
   - **Git Commit**: Every 30 minutes

2. **Integration Testing** (Day 23)
   - User flow tests
   - API integration tests
   - State management tests
   - **Git Commit**: Every 30 minutes

3. **E2E Testing** (Day 24)
   - Critical path tests
   - Cross-browser tests
   - Mobile tests
   - **Git Commit**: Every 30 minutes

4. **Documentation** (Day 25)
   - Component documentation
   - Storybook setup
   - Usage examples
   - Style guide
   - **Git Commit**: Every 30 minutes

**Success Criteria**:
- ✓ Test coverage >80%
- ✓ All tests passing
- ✓ Documentation complete
- ✓ Storybook running

**QA Checkpoints**:
- [ ] Unit tests comprehensive
- [ ] E2E tests cover critical paths
- [ ] Documentation clear
- [ ] Examples working

## API Integration

### API Client Setup
```typescript
// src/services/api-client.ts
class APIClient {
  private baseURL: string;
  private token: string | null;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL!;
  }

  async request<T>(
    endpoint: string,
    options?: RequestOptions
  ): Promise<T> {
    // Implementation with retry, error handling
  }
}
```

### Service Layer
```typescript
// src/services/
- authService.ts      # Login, logout, refresh
- userService.ts      # User CRUD operations
- permissionService.ts # Permission management
- clientService.ts    # Client operations
- analyticsService.ts # Analytics data
- auditService.ts     # Audit log retrieval
```

## Error Handling

### Error Boundary
```typescript
// src/components/ErrorBoundary.tsx
- Catches React errors
- Shows user-friendly error page
- Logs to monitoring service
- Provides recovery action
```

### API Error Handling
```typescript
// Standard error format
interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// Error handling strategies
- Retry with exponential backoff
- Show toast for user errors
- Log system errors
- Fallback UI for critical errors
```

## Performance Optimization

### Strategies
1. **Code Splitting**
   - Route-based splitting
   - Component lazy loading
   - Dynamic imports

2. **Caching**
   - React Query caching
   - Static asset caching
   - API response caching

3. **Optimization**
   - Image optimization (next/image)
   - Font optimization
   - Bundle size monitoring

### Performance Targets
- First Contentful Paint: <1.5s
- Time to Interactive: <3s
- Cumulative Layout Shift: <0.1
- Bundle size: <500KB initial

## Security Considerations

### Frontend Security
1. **XSS Prevention**
   - Input sanitization
   - Content Security Policy
   - Secure cookie handling

2. **Authentication**
   - JWT token storage (httpOnly cookies)
   - Automatic token refresh
   - Session timeout handling

3. **Data Protection**
   - No sensitive data in localStorage
   - API key protection
   - Environment variable security

## Testing Strategy

### Unit Tests
```typescript
// Example test
describe('UserTable', () => {
  it('should render user data correctly', () => {
    // Test implementation
  });
});
```

### Integration Tests
- API integration tests
- State management tests
- Router integration tests

### E2E Tests
```typescript
// playwright/tests/auth.spec.ts
test('user can login', async ({ page }) => {
  // E2E test implementation
});
```

## Common Error Patterns & Solutions

### 1. Hydration Errors
**Problem**: Client/server mismatch in Next.js
**Solution**: Use `useEffect` for client-only code, check for `window` object

### 2. State Management Issues
**Problem**: Stale state or race conditions
**Solution**: Use React Query for server state, Zustand for UI state

### 3. Performance Issues
**Problem**: Large bundle sizes or slow renders
**Solution**: Code splitting, memoization, virtual scrolling

### 4. Type Errors
**Problem**: TypeScript compilation errors
**Solution**: Strict type checking, proper type definitions

## Agent Responsibilities

### Frontend Agent 1 - UI/UX Components
- Shadcn UI implementation
- Layout components
- Theme system
- Responsive design

### Frontend Agent 2 - State Management
- Authentication flow
- Zustand stores
- React Query setup
- Data fetching logic

### Frontend Agent 3 - Forms & Validation
- Form components
- Validation schemas
- Error handling
- User feedback

### Frontend Agent 4 - Dashboard & Analytics
- Chart components
- Real-time updates
- Data visualization
- Export functionality

## Deployment Considerations

### Build Configuration
```javascript
// next.config.js
module.exports = {
  output: 'standalone',
  images: {
    domains: ['your-domain.com'],
  },
  // Other configurations
};
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_APP_URL=
NEXT_PUBLIC_GA_MEASUREMENT_ID=
```

## Monitoring & Analytics

### Frontend Monitoring
- Error tracking (Sentry)
- Performance monitoring
- User analytics
- Custom event tracking

### Metrics to Track
- Page load times
- API response times
- Error rates
- User interactions

---

**Document Version**: 1.0.0  
**Last Updated**: 2024-01-20  
**Dependencies**: main-spec.md, backend-spec.md