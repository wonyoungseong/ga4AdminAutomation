/**
 * Type-Safe API Client
 * 
 * This client provides type-safe access to the FastAPI backend
 * with proper error handling, response validation, and data normalization.
 */

import {
  User, UserCreate, UserUpdate, UserRegistrationRequest, UserApprovalRequest,
  EmailVerificationRequest, PendingUser,
  Client, ClientCreate, ClientUpdate,
  ServiceAccount, ServiceAccountUpdate,
  GA4Property,
  PropertyAccessRequest, PropertyAccessRequestCreate, PropertyAccessRequestResponse,
  AuditLog, UserActivityLog, UserActivityLogResponse,
  DashboardStats, SystemStats,
  LoginRequest, LoginResponse, SessionInfo,
  PaginatedResponse,
  PaginatedResponseLegacy,
  SyncStatus,
  isPaginatedResponse,
  isServiceAccount,
  isPendingUser,
  isPropertyAccessRequest,
  ApiError,
  isApiError
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: string,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiClientError';
  }

  static fromResponse(response: Response, data?: any): ApiClientError {
    const message = data?.message || data?.detail || `HTTP ${response.status}: ${response.statusText}`;
    return new ApiClientError(
      message,
      response.status,
      data?.detail,
      data?.code
    );
  }
}

// Session management interface
interface SessionManager {
  getToken(): string | null;
  setToken(token: string, refreshToken?: string): void;
  removeToken(): void;
  isTokenExpired(): boolean;
  refreshToken(): Promise<string | null>;
}

// Browser-based session manager implementation
class BrowserSessionManager implements SessionManager {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly TOKEN_EXPIRY_KEY = 'token_expiry';

  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  setToken(token: string, refreshToken?: string): void {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem(this.TOKEN_KEY, token);
    if (refreshToken) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }
    
    // Extract expiry from JWT token
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.exp) {
        localStorage.setItem(this.TOKEN_EXPIRY_KEY, payload.exp.toString());
      }
    } catch (error) {
      console.warn('Failed to parse token expiry:', error);
    }
  }

  removeToken(): void {
    if (typeof window === 'undefined') return;
    
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
  }

  isTokenExpired(): boolean {
    if (typeof window === 'undefined') return true;
    
    const token = localStorage.getItem(this.TOKEN_KEY);
    if (!token) return true;
    
    const expiryStr = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiryStr) return false; // Assume valid if no expiry info
    
    const expiry = parseInt(expiryStr, 10);
    const now = Math.floor(Date.now() / 1000);
    
    // Add 60 second buffer to account for network delays
    return now >= (expiry - 60);
  }

  async refreshToken(): Promise<string | null> {
    if (typeof window === 'undefined') return null;
    
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      console.log('No refresh token available');
      return null;
    }
    
    try {
      console.log('Attempting to refresh token...');
      const response = await fetch(`${API_BASE_URL}/api/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.log('Refresh token request failed:', response.status, response.statusText);
        // Refresh token is invalid, clear all tokens
        this.removeToken();
        return null;
      }
      
      const data = await response.json();
      if (data.access_token) {
        console.log('Token refresh successful');
        this.setToken(data.access_token, data.refresh_token);
        return data.access_token;
      }
      
      console.log('No access token in refresh response');
      return null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.removeToken();
      return null;
    }
  }
}

export class TypeSafeApiClient {
  private sessionManager: SessionManager;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.sessionManager = new BrowserSessionManager();
  }

  private getAuthHeader(): Record<string, string> {
    const token = this.sessionManager.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeader(),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle authentication errors
      if (response.status === 401) {
        // Don't auto-redirect here, let the auth context handle it
        // Use the refresh promise to prevent multiple concurrent refresh attempts
        if (!this.refreshPromise) {
          this.refreshPromise = this.sessionManager.refreshToken().finally(() => {
            this.refreshPromise = null;
          });
        }
        
        const refreshedToken = await this.refreshPromise;
        if (refreshedToken) {
          // Retry the request with new token
          const retryHeaders = {
            ...headers,
            Authorization: `Bearer ${refreshedToken}`
          };
          
          const retryResponse = await fetch(url, {
            ...options,
            headers: retryHeaders,
          });
          
          if (retryResponse.ok) {
            const retryContentType = retryResponse.headers.get('content-type');
            if (retryContentType?.includes('application/json')) {
              return await retryResponse.json() as T;
            } else {
              return await retryResponse.text() as T;
            }
          }
        }
        
        // If refresh failed or retry failed, throw error without redirecting
        throw new ApiClientError('Authentication required', 401);
      }

      // Parse response
      let data: unknown;
      const contentType = response.headers.get('content-type');
      
      if (contentType?.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      // Handle HTTP errors
      if (!response.ok) {
        throw ApiClientError.fromResponse(response, data);
      }

      return data as T;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiClientError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  // ===== Authentication & Session Management =====

  async login(email: string, password: string): Promise<LoginResponse> {
    const credentials: LoginRequest = { email, password };
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw ApiClientError.fromResponse(response, errorData);
      }

      const loginData: LoginResponse = await response.json();
      
      // Store tokens in session manager
      this.sessionManager.setToken(loginData.access_token, loginData.refresh_token);
      
      console.log('Login successful, tokens stored');
      console.log('Access token stored:', loginData.access_token.substring(0, 20) + '...');
      console.log('Refresh token stored:', loginData.refresh_token ? loginData.refresh_token.substring(0, 20) + '...' : 'none');
      
      return loginData;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }
      throw new ApiClientError(`Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async logout(): Promise<void> {
    try {
      // Call logout endpoint if available
      await this.request('/api/auth/logout', { method: 'POST' });
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      // Always clear local session
      this.sessionManager.removeToken();
    }
  }

  async refreshAuthToken(): Promise<string | null> {
    // Use the same refresh promise to prevent concurrent refresh attempts
    if (!this.refreshPromise) {
      this.refreshPromise = this.sessionManager.refreshToken().finally(() => {
        this.refreshPromise = null;
      });
    }
    return this.refreshPromise;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  getSessionInfo(): SessionInfo | null {
    const token = this.sessionManager.getToken();
    if (!token) return null;
    
    try {
      // Decode JWT to get expiration (basic implementation)
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        user: payload.user || {},
        token,
        expires_at: new Date(payload.exp * 1000).toISOString(),
      } as SessionInfo;
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    const token = this.sessionManager.getToken();
    return token !== null && !this.sessionManager.isTokenExpired();
  }

  // ===== Dashboard =====

  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/api/dashboard/stats');
  }

  // ===== User Management =====

  async getUsers(
    page: number = 1, 
    limit: number = 10,
    filters?: {
      role?: string;
      status?: string;
      registration_status?: string;
    }
  ): Promise<PaginatedResponse<User>> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString(),
    });
    
    if (filters?.role) params.append('role', filters.role);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.registration_status) params.append('registration_status', filters.registration_status);

    const response = await this.request<User[]>(`/api/enhanced-users?${params}`);
    
    // Convert array response to paginated format
    return {
      items: Array.isArray(response) ? response : [],
      total: Array.isArray(response) ? response.length : 0,
      page,
      size: limit,
      pages: Math.ceil((Array.isArray(response) ? response.length : 0) / limit),
      has_next: false,
      has_prev: page > 1
    };
  }

  async getUserById(id: number): Promise<User> {
    return this.request<User>(`/api/enhanced-users/${id}`);
  }

  async createUser(userData: UserCreate): Promise<User> {
    return this.request<User>('/api/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async registerUser(userData: UserRegistrationRequest): Promise<User> {
    return this.request<User>('/api/enhanced-users/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async verifyEmail(token: string): Promise<{ message: string }> {
    const requestData: EmailVerificationRequest = { token };
    return this.request<{ message: string }>('/api/enhanced-users/verify-email', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  async updateUser(id: number, userData: UserUpdate): Promise<User> {
    return this.request<User>(`/api/enhanced-users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/enhanced-users/${id}`, {
      method: 'DELETE',
    });
  }

  // ===== Pending User Management =====

  async getPendingUsers(
    page: number = 1, 
    limit: number = 50
  ): Promise<PaginatedResponse<PendingUser>> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString(),
    });

    const response = await this.request<User[]>(`/api/enhanced-users/pending-approval?${params}`);
    
    // Convert User[] to PendingUser[] and create paginated response
    const pendingUsers: PendingUser[] = (Array.isArray(response) ? response : []).map(user => ({
      id: user.id,
      email: user.email,
      name: user.name,
      company: user.company,
      department: user.department,
      job_title: user.job_title,
      phone_number: user.phone_number,
      requested_client_id: user.primary_client_id,
      registration_status: user.registration_status,
      created_at: user.created_at,
    }));
    
    return {
      items: pendingUsers,
      total: pendingUsers.length,
      page,
      size: limit,
      pages: Math.ceil(pendingUsers.length / limit),
      has_next: false,
      has_prev: page > 1
    };
  }

  async approveUser(
    userId: number, 
    approvalData: UserApprovalRequest
  ): Promise<User> {
    return this.request<User>(`/api/enhanced-users/${userId}/approve`, {
      method: 'POST',
      body: JSON.stringify(approvalData),
    });
  }

  async rejectUser(
    userId: number, 
    rejectionReason: string
  ): Promise<User> {
    const approvalData: UserApprovalRequest = {
      approved: false,
      rejection_reason: rejectionReason,
    };
    return this.request<User>(`/api/enhanced-users/${userId}/approve`, {
      method: 'POST',
      body: JSON.stringify(approvalData),
    });
  }

  // ===== Clients =====

  async getClients(page: number = 1, limit: number = 10): Promise<PaginatedResponse<Client>> {
    const response = await this.request<PaginatedResponse<Client> | PaginatedResponseLegacy<Client>>(
      `/api/clients?page=${page}&limit=${limit}`
    );
    
    return this.normalizePaginatedResponse(response, 'clients');
  }

  async getClientById(id: number): Promise<Client> {
    return this.request<Client>(`/api/clients/${id}`);
  }

  async createClient(clientData: ClientCreate): Promise<Client> {
    return this.request<Client>('/api/clients', {
      method: 'POST',
      body: JSON.stringify(clientData),
    });
  }

  async updateClient(id: number, clientData: ClientUpdate): Promise<Client> {
    return this.request<Client>(`/api/clients/${id}`, {
      method: 'PUT',
      body: JSON.stringify(clientData),
    });
  }

  async deleteClient(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/clients/${id}`, {
      method: 'DELETE',
    });
  }

  // ===== Service Accounts =====

  async getServiceAccounts(
    page: number = 1,
    limit: number = 20,
    client_id?: number
  ): Promise<PaginatedResponse<ServiceAccount>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (client_id) params.append('client_id', client_id.toString());

    const response = await this.request<PaginatedResponse<ServiceAccount> | PaginatedResponseLegacy<ServiceAccount>>(
      `/api/service-accounts?${params}`
    );
    
    const normalized = this.normalizePaginatedResponse(response, 'service_accounts');
    
    // Normalize service account data
    normalized.items = normalized.items.map(sa => this.normalizeServiceAccount(sa as unknown as Record<string, unknown>));
    
    return normalized;
  }

  async getServiceAccountById(id: number): Promise<ServiceAccount> {
    const response = await this.request<ServiceAccount>(`/api/service-accounts/${id}`);
    return this.normalizeServiceAccount(response as unknown as Record<string, unknown>);
  }

  async createServiceAccount(serviceAccountData: FormData): Promise<ServiceAccount> {
    const url = `${API_BASE_URL}/api/service-accounts`;
    const headers = {
      ...this.getAuthHeader(),
      // Don't set Content-Type for FormData
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: serviceAccountData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
      }
      const error = await response.json().catch(() => ({}));
      throw new ApiClientError(
        error.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        error.detail
      );
    }

    const data = await response.json();
    return this.normalizeServiceAccount(data as unknown as Record<string, unknown>);
  }

  async updateServiceAccount(id: number, serviceAccountData: ServiceAccountUpdate): Promise<ServiceAccount> {
    const response = await this.request<ServiceAccount>(`/api/service-accounts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(serviceAccountData),
    });
    return this.normalizeServiceAccount(response as unknown as Record<string, unknown>);
  }

  async deleteServiceAccount(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/service-accounts/${id}`, {
      method: 'DELETE',
    });
  }

  async discoverGA4Properties(serviceAccountId: number): Promise<GA4Property[]> {
    return this.request<GA4Property[]>(`/api/service-accounts/${serviceAccountId}/discover-properties`, {
      method: 'POST',
    });
  }

  async syncServiceAccountPermissions(serviceAccountId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/service-accounts/${serviceAccountId}/sync-permissions`, {
      method: 'POST',
    });
  }

  async testServiceAccountHealth(serviceAccountId: number): Promise<{ health_status: string; health_checked_at: string }> {
    return this.request<{ health_status: string; health_checked_at: string }>(`/api/service-accounts/${serviceAccountId}/health/check`, {
      method: 'POST',
    });
  }

  // ===== GA4 Properties =====

  async getGA4PropertiesManagement(
    page: number = 1,
    limit: number = 20,
    service_account_id?: number,
    client_id?: number
  ): Promise<PaginatedResponse<GA4Property>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (service_account_id) params.append('service_account_id', service_account_id.toString());
    if (client_id) params.append('client_id', client_id.toString());

    const response = await this.request<PaginatedResponse<GA4Property> | PaginatedResponseLegacy<GA4Property>>(
      `/api/ga4-properties?${params}`
    );
    
    return this.normalizePaginatedResponse(response, 'properties');
  }

  // ===== Audit Logs =====

  async getAuditLogs(
    page: number = 1,
    limit: number = 50,
    filters?: Record<string, string>
  ): Promise<PaginatedResponse<AuditLog>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (filters) {
      if (filters.action) params.append('action', filters.action);
      if (filters.user_email) params.append('user_email', filters.user_email);
      if (filters.target_type) params.append('target_type', filters.target_type);
      if (filters.status) params.append('status', filters.status);
    }
    
    const response = await this.request<PaginatedResponse<AuditLog>>(
      `/api/audit-logs?${params}`
    );
    
    // Ensure we return a properly structured response
    if (!isPaginatedResponse<AuditLog>(response)) {
      const responseArray = Array.isArray(response) ? response as AuditLog[] : [];
      return {
        items: responseArray,
        total: responseArray.length,
        page,
        size: limit,
        pages: Math.ceil(responseArray.length / limit),
        has_next: false,
        has_prev: page > 1
      };
    }
    
    return response;
  }

  async getAuditLogStats(): Promise<{
    total_logs?: number;
    success_logs?: number;
    failure_logs?: number;
    warning_logs?: number;
  }> {
    return this.request<{
      total_logs?: number;
      success_logs?: number;
      failure_logs?: number;
      warning_logs?: number;
    }>('/api/audit-logs/stats');
  }

  // ===== Property Access Requests =====

  async getPropertyAccessRequests(
    page: number = 1,
    limit: number = 20,
    filters?: {
      status?: string;
      user_id?: number;
      client_id?: number;
    }
  ): Promise<PaginatedResponse<PropertyAccessRequestResponse>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (filters?.status) params.append('status', filters.status);
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.client_id) params.append('client_id', filters.client_id.toString());

    return this.request<PaginatedResponse<PropertyAccessRequestResponse>>(
      `/api/permission-requests?${params}`
    );
  }

  async createPropertyAccessRequest(
    requestData: PropertyAccessRequestCreate
  ): Promise<PropertyAccessRequestResponse> {
    return this.request<PropertyAccessRequestResponse>('/api/enhanced-users/property-access-request', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  async approvePropertyAccessRequest(
    requestId: number,
    approvalData?: { expires_in_days?: number }
  ): Promise<PropertyAccessRequestResponse> {
    return this.request<PropertyAccessRequestResponse>(`/api/permission-requests/${requestId}/approve`, {
      method: 'POST',
      body: JSON.stringify(approvalData || {}),
    });
  }

  async denyPropertyAccessRequest(
    requestId: number,
    denialReason: string
  ): Promise<PropertyAccessRequestResponse> {
    return this.request<PropertyAccessRequestResponse>(`/api/permission-requests/${requestId}/deny`, {
      method: 'POST',
      body: JSON.stringify({ denial_reason: denialReason }),
    });
  }

  async revokePropertyAccess(
    requestId: number,
    revocationReason: string
  ): Promise<PropertyAccessRequestResponse> {
    return this.request<PropertyAccessRequestResponse>(`/api/permission-requests/${requestId}/revoke`, {
      method: 'POST',
      body: JSON.stringify({ revocation_reason: revocationReason }),
    });
  }

  async getClientProperties(clientId: number): Promise<GA4Property[]> {
    return this.request<GA4Property[]>(`/api/permission-requests/clients/${clientId}/properties`);
  }

  // ===== Permission Requests Management =====

  async getMyPermissionRequests(
    status?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (status) params.append('status', status);

    const response = await this.request<any[]>(`/api/permission-requests/my-requests?${params}`);
    return Array.isArray(response) ? response : [];
  }

  async getPendingApprovalRequests(
    limit: number = 50,
    offset: number = 0
  ): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await this.request<any[]>(`/api/permission-requests/pending-approvals?${params}`);
    return Array.isArray(response) ? response : [];
  }

  async submitPermissionRequest(requestData: {
    client_id: number;
    ga_property_id: string;
    target_email: string;
    permission_level: string;
    business_justification: string;
    requested_duration_days: number;
  }): Promise<any> {
    return this.request<any>('/api/permission-requests/', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  async approvePermissionRequest(
    requestId: number,
    processingNotes?: string
  ): Promise<any> {
    return this.request<any>(`/api/permission-requests/${requestId}/approve`, {
      method: 'PUT',
      body: JSON.stringify({ processing_notes: processingNotes }),
    });
  }

  async rejectPermissionRequest(
    requestId: number,
    processingNotes: string
  ): Promise<any> {
    return this.request<any>(`/api/permission-requests/${requestId}/reject`, {
      method: 'PUT',
      body: JSON.stringify({ processing_notes: processingNotes }),
    });
  }

  async cancelPermissionRequest(requestId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/permission-requests/${requestId}`, {
      method: 'DELETE',
    });
  }

  async getAutoApprovalRules(): Promise<{
    rules: any[];
    user_role: string;
  }> {
    return this.request<{
      rules: any[];
      user_role: string;
    }>('/api/permission-requests/auto-approval-rules');
  }

  // ===== User Activity & Audit Logs =====

  async getUserActivityLogs(
    filters?: {
      user_id?: number;
      activity_type?: string;
      action?: string;
      date_from?: string;
      date_to?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<UserActivityLogResponse[]> {
    const params = new URLSearchParams();
    
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.activity_type) params.append('activity_type', filters.activity_type);
    if (filters?.action) params.append('action', filters.action);
    if (filters?.date_from) params.append('date_from', filters.date_from);
    if (filters?.date_to) params.append('date_to', filters.date_to);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());

    return this.request<UserActivityLogResponse[]>(`/api/enhanced-users/activity-logs?${params}`);
  }

  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>('/api/enhanced-users/system-stats');
  }

  async cleanupExpiredSessions(): Promise<{ message: string; cleaned_sessions: number }> {
    return this.request<{ message: string; cleaned_sessions: number }>('/api/enhanced-users/cleanup-sessions', {
      method: 'POST',
    });
  }

  // ===== Permissions Management =====

  async getPermissions(
    page: number = 1,
    limit: number = 50,
    filters?: {
      user_id?: number;
      client_id?: number;
      status?: string;
    }
  ): Promise<any[]> {
    const params = new URLSearchParams({
      skip: ((page - 1) * limit).toString(),
      limit: limit.toString(),
    });
    
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.client_id) params.append('client_id', filters.client_id.toString());
    if (filters?.status) params.append('status', filters.status);

    const response = await this.request<any[]>(`/api/permissions?${params}`);
    return Array.isArray(response) ? response : [];
  }

  async createPermission(permissionData: any): Promise<any> {
    return this.request<any>('/api/permissions', {
      method: 'POST',
      body: JSON.stringify(permissionData),
    });
  }

  async updatePermission(id: number, permissionData: any): Promise<any> {
    return this.request<any>(`/api/permissions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(permissionData),
    });
  }

  async deletePermission(id: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/permissions/${id}`, {
      method: 'DELETE',
    });
  }

  // ===== Utility Methods =====

  private normalizePaginatedResponse<T>(
    response: PaginatedResponse<T> | PaginatedResponseLegacy<T> | Record<string, unknown>,
    legacyKey: string
  ): PaginatedResponse<T> {
    if (isPaginatedResponse<T>(response)) {
      return response;
    }

    // Handle legacy response format
    const responseObj = response as Record<string, unknown>;
    const items = (responseObj[legacyKey] as T[]) || (responseObj.items as T[]) || [];
    const total = (responseObj.total as number) || 0;
    const page = (responseObj.page as number) || 1;
    const size = (responseObj.limit as number) || items.length;

    return {
      items: Array.isArray(items) ? items : [],
      total,
      page,
      size,
      pages: size > 0 ? Math.ceil(total / size) : 0,
      has_next: page * size < total,
      has_prev: page > 1
    };
  }

  private normalizeServiceAccount(sa: Record<string, unknown>): ServiceAccount {
    if (!isServiceAccount(sa)) {
      console.warn('Invalid service account data:', sa);
    }

    const serviceAccount = sa as unknown as ServiceAccount;
    return {
      ...serviceAccount,
      // Map backend field names to frontend expectations
      name: (sa.display_name as string) || (sa.name as string) || (serviceAccount.email?.split('@')[0]) || 'Unknown',
      health_checked_at: (sa.health_checked_at as string) || (sa.last_health_check as string),
      properties_count: (sa.properties_count as number) || 0,
      permissions_sync_status: (sa.permissions_sync_status as SyncStatus) || 'never',
      last_sync: (sa.last_sync as string) || (sa.synchronized_at as string),
      description: (sa.description as string) || '',
      private_key_id: (sa.private_key_id as string) || (sa.key_version as number)?.toString(),
      credentials_file_name: (sa.credentials_file_name as string) || `${serviceAccount.email}-credentials.json`
    };
  }
}

// Type guard for API error responses (if not imported)
function isApiErrorLocal(obj: unknown): obj is ApiError {
  return typeof obj === 'object' && obj !== null && 'message' in obj && typeof (obj as ApiError).message === 'string';
}

export const typeSafeApiClient = new TypeSafeApiClient();
export { ApiClientError, BrowserSessionManager };
export type { SessionManager };