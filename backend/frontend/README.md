# GA4 Admin Frontend

Role-based access control (RBAC) frontend for Google Analytics 4 permission management system.

## Features

### Role-Based Access Control
- **Super Admin**: Full system access, user management, system settings
- **Admin**: User management, client management, permission approvals
- **Requester**: Create permission requests, view own requests
- **GA User**: View own permissions, read-only access

### Core Functionality
- **Authentication**: Secure login/logout with JWT tokens
- **Role-based Navigation**: Dynamic menu based on user permissions
- **Permission Guards**: Component-level access control
- **Dashboard Widgets**: Role-specific dashboard content
- **User Management**: CRUD operations for user accounts
- **Permission Management**: Request, approve, track GA4 permissions
- **Audit Logging**: Track all system activities

### UI Components
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Accessible Components**: WCAG compliant UI using Radix UI primitives
- **Modern Interface**: Clean, professional design with shadcn/ui
- **Interactive Elements**: Dropdowns, modals, forms with validation

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Radix UI primitives with shadcn/ui
- **State Management**: React Context for authentication
- **API Client**: Custom fetch-based client with error handling
- **Icons**: Lucide React icon library

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Demo Credentials

Use these credentials to test different roles:

- **Super Admin**: `superadmin@example.com` / `password123`
- **Admin**: `admin@example.com` / `password123` 
- **Requester**: `requester@example.com` / `password123`
- **GA User**: `gauser@example.com` / `password123`

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Protected dashboard pages
│   └── layout.tsx         # Root layout with providers
├── components/            # Reusable React components
│   ├── auth/              # Authentication components
│   ├── dashboard/         # Dashboard-specific widgets
│   ├── layout/            # Layout components (sidebar, header)
│   └── ui/                # Base UI components (shadcn/ui)
├── contexts/              # React contexts
│   └── auth-context.tsx   # Authentication state management
├── lib/                   # Utility libraries
│   ├── api.ts             # API client
│   └── utils.ts           # Helper functions
└── types/                 # TypeScript type definitions
    └── auth.ts            # Authentication & RBAC types
```

## Key Components

### Authentication Context
Manages authentication state, JWT tokens, and role-based permissions:
- Automatic token refresh
- Role-based access control
- Persistent authentication state

### Permission Guards
Protect components and routes based on user roles and permissions:
```tsx
<PermissionGuard requiredRoles={[UserRole.ADMIN]}>
  <AdminOnlyComponent />
</PermissionGuard>
```

### Role-based Navigation
Dynamic sidebar navigation based on user permissions:
- Automatically shows/hides menu items
- Role-specific quick actions
- Hierarchical menu structure

### Dashboard Widgets
Customizable widgets that adapt to user roles:
- Admin: System stats, pending approvals, recent activity
- User: Personal stats, request status, quick actions

## API Integration

The frontend integrates with the RBAC backend API:

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout  
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Current user info

### User Management
- `GET /users` - List users (Admin only)
- `PUT /users/{id}` - Update user (Admin only)
- `DELETE /users/{id}` - Delete user (Super Admin only)

### Permission Management
- `GET /permissions` - List permissions
- `POST /permissions` - Create request
- `POST /permissions/{id}/approve` - Approve request
- `POST /permissions/{id}/reject` - Reject request

## Security Features

### Client-side Security
- JWT token management with automatic refresh
- Role-based route protection
- Component-level permission guards
- Secure token storage in localStorage

### Input Validation
- Form validation with error handling
- Type-safe API requests
- CSRF protection through SameSite cookies

## Performance Optimizations

### Code Splitting
- Automatic route-based code splitting
- Lazy loading of dashboard components
- Optimized bundle sizes

### Caching Strategy
- API response caching
- Static asset optimization
- Efficient re-rendering with React optimizations

## Accessibility

### WCAG Compliance
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes

### Responsive Design
- Mobile-first approach
- Touch-friendly interface
- Adaptive layouts for all screen sizes

## Development

### Code Quality
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Building
npm run build
```

### Environment Variables
- `NEXT_PUBLIC_API_BASE_URL`: Public API base URL
- `API_BASE_URL`: Server-side API base URL

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Contributing

1. Follow TypeScript best practices
2. Use the established component patterns
3. Maintain RBAC security boundaries
4. Add proper error handling
5. Include accessibility features
6. Write responsive CSS

## License

This project is part of the GA4 Admin Automation System.