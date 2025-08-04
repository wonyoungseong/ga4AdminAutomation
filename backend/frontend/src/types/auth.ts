/**
 * Authentication and RBAC Types
 * Matches backend schemas and enums
 */

// User Roles (matches backend UserRole enum)
export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  REQUESTER = 'requester',
  GA_USER = 'ga_user',
}

// User Status (matches backend UserStatus enum)
export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
}

// Permission Levels (matches backend PermissionLevel enum)
export enum PermissionLevel {
  VIEWER = 'viewer',
  ANALYST = 'analyst',
  MARKETER = 'marketer',
  EDITOR = 'editor',
  ADMINISTRATOR = 'administrator',
}

// Permission Status (matches backend PermissionStatus enum)
export enum PermissionStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  REVOKED = 'revoked',
}

// User interface (matches backend UserResponse schema)
export interface User {
  id: number;
  email: string;
  name: string;
  company?: string;
  role: UserRole;
  status: UserStatus;
  is_representative: boolean;
  created_at: string;
  last_login_at?: string;
}

// Auth Token interface (matches backend Token schema)
export interface AuthToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Login request interface (matches backend UserLogin schema)
export interface LoginRequest {
  email: string;
  password: string;
}

// User registration interface (matches backend UserCreate schema)
export interface RegisterRequest {
  email: string;
  name: string;
  company?: string;
  password: string;
}

// Auth Context interface
export interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

// Client interface (matches backend ClientResponse schema)
export interface Client {
  id: number;
  name: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Service Account interface (matches backend ServiceAccountResponse schema)
export interface ServiceAccount {
  id: number;
  client_id: number;
  email: string;
  display_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Permission Grant interface (matches backend PermissionGrantResponse schema)
export interface PermissionGrant {
  id: number;
  user_id: number;
  client_id: number;
  service_account_id: number;
  ga_property_id: string;
  target_email: string;
  permission_level: PermissionLevel;
  status: PermissionStatus;
  expires_at?: string;
  approved_at?: string;
  approved_by_id?: number;
  reason?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Audit Log interface (matches backend AuditLogResponse schema)
export interface AuditLog {
  id: number;
  actor_id?: number;
  permission_grant_id?: number;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  created_at: string;
}

// Notification interface (matches backend NotificationResponse schema)
export interface Notification {
  id: number;
  recipient_email: string;
  subject: string;
  message: string;
  notification_type: string;
  sent_at?: string;
  created_at: string;
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// Paginated response interface (matches backend PaginatedResponse schema)
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

// Role-based permissions mapping
export const RolePermissions: Record<UserRole, string[]> = {
  [UserRole.SUPER_ADMIN]: [
    'users.create',
    'users.read',
    'users.update',
    'users.delete',
    'users.manage_roles',
    'clients.create',
    'clients.read',
    'clients.update',
    'clients.delete',
    'service_accounts.create',
    'service_accounts.read',
    'service_accounts.update',
    'service_accounts.delete',
    'permissions.create',
    'permissions.read',
    'permissions.update',
    'permissions.delete',
    'permissions.approve',
    'permissions.reject',
    'audit_logs.read',
    'dashboard.admin',
    'system.manage',
  ],
  [UserRole.ADMIN]: [
    'users.read',
    'users.update',
    'users.manage_roles',
    'clients.create',
    'clients.read',
    'clients.update',
    'clients.delete',
    'service_accounts.create',
    'service_accounts.read',
    'service_accounts.update',
    'service_accounts.delete',
    'permissions.create',
    'permissions.read',
    'permissions.update',
    'permissions.approve',
    'permissions.reject',
    'audit_logs.read',
    'dashboard.admin',
  ],
  [UserRole.REQUESTER]: [
    'users.read_own',
    'users.update_own',
    'permissions.create',
    'permissions.read_own',
    'audit_logs.read_own',
    'dashboard.user',
  ],
  [UserRole.GA_USER]: [
    'users.read_own',
    'permissions.read_own',
    'dashboard.readonly',
  ],
};

// Navigation items based on roles
export interface NavItem {
  title: string;
  href: string;
  icon?: string;
  description?: string;
  permissions?: string[];
  children?: NavItem[];
}

export const NavigationItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: 'LayoutDashboard',
    permissions: ['dashboard.admin', 'dashboard.user', 'dashboard.readonly'],
  },
  {
    title: 'Users',
    href: '/dashboard/users',
    icon: 'Users',
    permissions: ['users.read', 'users.manage_roles'],
    children: [
      {
        title: 'All Users',
        href: '/dashboard/users',
        permissions: ['users.read'],
      },
      {
        title: 'Role Management',
        href: '/dashboard/users/roles',
        permissions: ['users.manage_roles'],
      },
    ],
  },
  {
    title: 'Clients',
    href: '/dashboard/clients',
    icon: 'Building2',
    permissions: ['clients.read'],
  },
  {
    title: 'Service Accounts',
    href: '/dashboard/service-accounts',
    icon: 'Key',
    permissions: ['service_accounts.read'],
  },
  {
    title: 'Permissions',
    href: '/dashboard/permissions',
    icon: 'Shield',
    permissions: ['permissions.read', 'permissions.read_own'],
    children: [
      {
        title: 'All Permissions',
        href: '/dashboard/permissions',
        permissions: ['permissions.read'],
      },
      {
        title: 'My Requests',
        href: '/dashboard/permissions/my-requests',
        permissions: ['permissions.read_own'],
      },
      {
        title: 'Pending Approvals',
        href: '/dashboard/permissions/pending',
        permissions: ['permissions.approve'],
      },
    ],
  },
  {
    title: 'Audit Logs',
    href: '/dashboard/audit-logs',
    icon: 'FileText',
    permissions: ['audit_logs.read', 'audit_logs.read_own'],
  },
  {
    title: 'My Profile',
    href: '/dashboard/profile',
    icon: 'User',
    permissions: ['users.read_own'],
  },
];