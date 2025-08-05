/**
 * API Types - Aligned with Backend FastAPI Schemas
 * 
 * This file contains type definitions that match the backend Pydantic schemas
 * to ensure frontend-backend compatibility and type safety.
 */

// ===== Base Types =====

export type UserRole = 'Super Admin' | 'Admin' | 'Requester' | 'Viewer';
export type UserStatus = 'active' | 'inactive' | 'suspended';
export type RegistrationStatus = 'pending_verification' | 'verified' | 'approved' | 'rejected';
export type PermissionLevel = 'read' | 'edit' | 'manage';
export type PermissionStatus = 'active' | 'expired' | 'revoked' | 'pending';
export type HealthStatus = 'healthy' | 'warning' | 'error' | 'unknown';
export type SyncStatus = 'synced' | 'pending' | 'error' | 'never';
export type PropertyAccessStatus = 'requested' | 'approved' | 'denied' | 'revoked' | 'expired';
export type PriorityLevel = 'low' | 'medium' | 'high' | 'critical';
export type ActivityType = 'auth' | 'user_management' | 'permission_management' | 'audit';

// ===== User Types =====

export interface User {
  id: number;
  email: string;
  name: string;
  company?: string;
  role: UserRole;
  status: UserStatus;
  registration_status: RegistrationStatus;
  is_representative: boolean;
  email_verified_at?: string;
  approved_at?: string;
  department?: string;
  job_title?: string;
  phone_number?: string;
  primary_client_id?: number;
  created_at: string;
  last_login_at?: string;
}

export interface PendingUser {
  id: number;
  email: string;
  name: string;
  company?: string;
  department?: string;
  job_title?: string;
  phone_number?: string;
  requested_client_id?: number;
  business_justification?: string;
  registration_status: RegistrationStatus;
  created_at: string;
}

export interface UserCreate {
  email: string;
  name: string;
  company?: string;
  password: string;
  role?: UserRole;
  requested_client_id?: number;
  business_justification?: string;
}

export interface UserRegistrationRequest {
  email: string;
  name: string;
  company?: string;
  password: string;
  department?: string;
  job_title?: string;
  phone_number?: string;
  requested_client_id?: number;
  business_justification?: string;
}

export interface UserApprovalRequest {
  approved: boolean;
  rejection_reason?: string;
  assigned_role?: UserRole;
  primary_client_id?: number;
}

export interface EmailVerificationRequest {
  token: string;
}

export interface UserUpdate {
  name?: string;
  company?: string;
  role?: UserRole;
  status?: UserStatus;
  registration_status?: RegistrationStatus;
  is_representative?: boolean;
  department?: string;
  job_title?: string;
  phone_number?: string;
  primary_client_id?: number;
}

// ===== Client Types =====

export interface Client {
  id: number;
  name: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  name: string;
  description?: string;
  contact_email?: string;
}

export interface ClientUpdate {
  name?: string;
  description?: string;
  contact_email?: string;
  is_active?: boolean;
}

// ===== Service Account Types =====

export interface ServiceAccount {
  id: number;
  client_id?: number;
  email: string;
  display_name?: string;
  project_id?: string;
  is_active: boolean;
  health_status: HealthStatus;
  health_checked_at?: string;
  last_used_at?: string;
  key_version?: number;
  created_at: string;
  updated_at: string;
  
  // Extended fields for frontend compatibility
  name?: string; // Computed from display_name or email
  client_name?: string;
  properties_count?: number;
  permissions_sync_status?: SyncStatus;
  last_sync?: string;
  last_health_check?: string;
  private_key_id?: string;
  credentials_file_name?: string;
  description?: string;
}

export interface ServiceAccountCreate {
  client_id: number;
  email: string;
  secret_name: string;
  display_name?: string;
  project_id?: string;
  credentials_json?: string;
}

export interface ServiceAccountUpdate {
  display_name?: string;
  secret_name?: string;
  is_active?: boolean;
}

// ===== GA4 Property Types =====

export interface GA4Property {
  id: number;
  client_id?: number;
  property_id: string;
  display_name: string;
  service_account_id?: number;
  client_name?: string;
  is_active: boolean;
  last_access_check?: string;
  created_at: string;
  updated_at?: string;
}

// ===== Property Access Request Types =====

export interface PropertyAccessRequest {
  id: number;
  user_id: number;
  client_id: number;
  requested_property_id: string;
  target_email: string;
  permission_level: PermissionLevel;
  business_justification: string;
  requested_duration_days: number;
  priority_level: PriorityLevel;
  external_ticket_id?: string;
  status: PropertyAccessStatus;
  auto_approved: boolean;
  requires_approval_from_role?: UserRole;
  approved_by_id?: number;
  approved_at?: string;
  denied_at?: string;
  revoked_at?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyAccessRequestCreate {
  client_id: number;
  requested_property_id: string;
  target_email: string;
  permission_level: PermissionLevel;
  business_justification: string;
  requested_duration_days: number;
  priority_level: PriorityLevel;
  external_ticket_id?: string;
}

export interface PropertyAccessRequestResponse extends PropertyAccessRequest {
  user_name?: string;
  user_email?: string;
  client_name?: string;
  property_display_name?: string;
  approver_name?: string;
}

// ===== API Response Types =====

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
  has_next?: boolean;
  has_prev?: boolean;
}

// Legacy compatibility - used by existing components
export interface PaginatedResponseLegacy<T> {
  service_accounts?: T[];
  clients?: T[];
  properties?: T[];
  users?: T[];
  total: number;
  page?: number;
  limit?: number;
}

// ===== Dashboard Types =====

export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_service_accounts: number;
  healthy_service_accounts: number;
  total_properties: number;
  active_properties: number;
  total_clients?: number;
  active_permissions?: number;
  total_permissions?: number;
  total_audit_logs?: number;
  recent_activities?: Array<{
    id: number;
    action: string;
    user: string;
    timestamp: string;
    details?: string;
  }>;
}

// ===== Audit Log Types =====

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
  
  // Extended fields
  actor_name?: string;
  actor_email?: string;
}

// ===== Session & Authentication Types =====

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface SessionInfo {
  user: User;
  token: string;
  expires_at: string;
  refresh_token?: string;
}

// ===== Activity & Audit Types =====

export interface UserActivityLog {
  id: number;
  user_id: number;
  target_user_id?: number;
  client_id?: number;
  activity_type: ActivityType;
  action: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  details?: Record<string, any>;
  success: boolean;
  error_message?: string;
  duration_ms?: number;
  created_at: string;
}

export interface UserActivityLogResponse extends UserActivityLog {
  user_name?: string;
  user_email?: string;
  target_user_name?: string;
  target_user_email?: string;
  client_name?: string;
}

// ===== System Statistics Types =====

export interface SystemStats {
  users: {
    total: number;
    active: number;
    pending_verification: number;
    pending_approval: number;
    approved: number;
    rejected: number;
    suspended: number;
  };
  property_requests: {
    total: number;
    requested: number;
    approved: number;
    denied: number;
    revoked: number;
    expired: number;
  };
  client_assignments: {
    total: number;
    active: number;
    inactive: number;
    suspended: number;
  };
  activities: {
    total_activities: number;
    successful_activities: number;
    failed_activities: number;
    unique_users_today: number;
    unique_ips_today: number;
  };
}

// ===== Error Types =====

export interface ApiError {
  message: string;
  detail?: string;
  code?: string;
  status_code?: number;
}

// ===== Form Data Types =====

export interface ServiceAccountFormData {
  name: string;
  email: string;
  description: string;
  client_id: string;
  project_id: string;
  credentials_file: File | null;
}

// ===== Utility Types =====

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// ===== Type Guards =====

export function isApiError(obj: unknown): obj is ApiError {
  return typeof obj === 'object' && obj !== null && 'message' in obj && typeof (obj as ApiError).message === 'string';
}

export function isPaginatedResponse<T>(obj: unknown): obj is PaginatedResponse<T> {
  return typeof obj === 'object' && obj !== null && 'items' in obj && 'total' in obj &&
    Array.isArray((obj as PaginatedResponse<T>).items) && typeof (obj as PaginatedResponse<T>).total === 'number';
}

export function isServiceAccount(obj: unknown): obj is ServiceAccount {
  return typeof obj === 'object' && obj !== null && 
    'id' in obj && 'email' in obj && 'is_active' in obj &&
    typeof (obj as ServiceAccount).id === 'number' && 
    typeof (obj as ServiceAccount).email === 'string' &&
    typeof (obj as ServiceAccount).is_active === 'boolean';
}

export function isPendingUser(obj: unknown): obj is PendingUser {
  return typeof obj === 'object' && obj !== null &&
    'id' in obj && 'email' in obj && 'registration_status' in obj &&
    typeof (obj as PendingUser).id === 'number' &&
    typeof (obj as PendingUser).email === 'string' &&
    typeof (obj as PendingUser).registration_status === 'string';
}

export function isPropertyAccessRequest(obj: unknown): obj is PropertyAccessRequest {
  return typeof obj === 'object' && obj !== null &&
    'id' in obj && 'user_id' in obj && 'status' in obj &&
    typeof (obj as PropertyAccessRequest).id === 'number' &&
    typeof (obj as PropertyAccessRequest).user_id === 'number' &&
    typeof (obj as PropertyAccessRequest).status === 'string';
}