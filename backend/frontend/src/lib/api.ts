/**
 * API client for backend communication
 */

import { 
  User, 
  AuthToken, 
  LoginRequest, 
  RegisterRequest,
  Client,
  ServiceAccount,
  PermissionGrant,
  AuditLog,
  Notification,
  ApiResponse,
  PaginatedResponse 
} from '@/types/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    
    // Load token from localStorage on client side
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // If response is not JSON, use the default error message
        }
        
        throw new Error(errorMessage);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response.text() as T;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<AuthToken> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    return this.makeRequest<AuthToken>('/auth/login', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    });
  }

  async register(userData: RegisterRequest): Promise<User> {
    return this.makeRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async refreshToken(): Promise<AuthToken> {
    return this.makeRequest<AuthToken>('/auth/refresh', {
      method: 'POST',
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.makeRequest<User>('/auth/me');
  }

  async logout(): Promise<void> {
    await this.makeRequest<void>('/auth/logout', {
      method: 'POST',
    });
  }

  // Users
  async getUsers(page: number = 1, size: number = 20): Promise<PaginatedResponse<User>> {
    return this.makeRequest<PaginatedResponse<User>>(`/users?page=${page}&size=${size}`);
  }

  async getUser(id: number): Promise<User> {
    return this.makeRequest<User>(`/users/${id}`);
  }

  async updateUser(id: number, userData: Partial<User>): Promise<User> {
    return this.makeRequest<User>(`/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(id: number): Promise<void> {
    await this.makeRequest<void>(`/users/${id}`, {
      method: 'DELETE',
    });
  }

  // Clients
  async getClients(page: number = 1, size: number = 20): Promise<PaginatedResponse<Client>> {
    return this.makeRequest<PaginatedResponse<Client>>(`/clients?page=${page}&size=${size}`);
  }

  async getClient(id: number): Promise<Client> {
    return this.makeRequest<Client>(`/clients/${id}`);
  }

  async createClient(clientData: Omit<Client, 'id' | 'created_at' | 'updated_at'>): Promise<Client> {
    return this.makeRequest<Client>('/clients', {
      method: 'POST',
      body: JSON.stringify(clientData),
    });
  }

  async updateClient(id: number, clientData: Partial<Client>): Promise<Client> {
    return this.makeRequest<Client>(`/clients/${id}`, {
      method: 'PUT',
      body: JSON.stringify(clientData),
    });
  }

  async deleteClient(id: number): Promise<void> {
    await this.makeRequest<void>(`/clients/${id}`, {
      method: 'DELETE',
    });
  }

  // Service Accounts
  async getServiceAccounts(page: number = 1, size: number = 20): Promise<PaginatedResponse<ServiceAccount>> {
    return this.makeRequest<PaginatedResponse<ServiceAccount>>(`/service-accounts?page=${page}&size=${size}`);
  }

  async getServiceAccount(id: number): Promise<ServiceAccount> {
    return this.makeRequest<ServiceAccount>(`/service-accounts/${id}`);
  }

  async createServiceAccount(accountData: Omit<ServiceAccount, 'id' | 'created_at' | 'updated_at'>): Promise<ServiceAccount> {
    return this.makeRequest<ServiceAccount>('/service-accounts', {
      method: 'POST',
      body: JSON.stringify(accountData),
    });
  }

  async updateServiceAccount(id: number, accountData: Partial<ServiceAccount>): Promise<ServiceAccount> {
    return this.makeRequest<ServiceAccount>(`/service-accounts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(accountData),
    });
  }

  async deleteServiceAccount(id: number): Promise<void> {
    await this.makeRequest<void>(`/service-accounts/${id}`, {
      method: 'DELETE',
    });
  }

  // Permission Grants
  async getPermissionGrants(page: number = 1, size: number = 20, userId?: number): Promise<PaginatedResponse<PermissionGrant>> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    
    if (userId) {
      params.append('user_id', userId.toString());
    }
    
    return this.makeRequest<PaginatedResponse<PermissionGrant>>(`/permissions?${params}`);
  }

  async getPermissionGrant(id: number): Promise<PermissionGrant> {
    return this.makeRequest<PermissionGrant>(`/permissions/${id}`);
  }

  async createPermissionGrant(grantData: Omit<PermissionGrant, 'id' | 'created_at' | 'updated_at' | 'status' | 'approved_at' | 'approved_by_id'>): Promise<PermissionGrant> {
    return this.makeRequest<PermissionGrant>('/permissions', {
      method: 'POST',
      body: JSON.stringify(grantData),
    });
  }

  async updatePermissionGrant(id: number, grantData: Partial<PermissionGrant>): Promise<PermissionGrant> {
    return this.makeRequest<PermissionGrant>(`/permissions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(grantData),
    });
  }

  async approvePermissionGrant(id: number, notes?: string): Promise<PermissionGrant> {
    return this.makeRequest<PermissionGrant>(`/permissions/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  async rejectPermissionGrant(id: number, notes?: string): Promise<PermissionGrant> {
    return this.makeRequest<PermissionGrant>(`/permissions/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  async deletePermissionGrant(id: number): Promise<void> {
    await this.makeRequest<void>(`/permissions/${id}`, {
      method: 'DELETE',
    });
  }

  // Audit Logs
  async getAuditLogs(page: number = 1, size: number = 20, userId?: number): Promise<PaginatedResponse<AuditLog>> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    
    if (userId) {
      params.append('user_id', userId.toString());
    }
    
    return this.makeRequest<PaginatedResponse<AuditLog>>(`/audit-logs?${params}`);
  }

  // Notifications
  async getNotifications(page: number = 1, size: number = 20): Promise<PaginatedResponse<Notification>> {
    return this.makeRequest<PaginatedResponse<Notification>>(`/notifications?page=${page}&size=${size}`);
  }

  // Dashboard Statistics
  async getDashboardStats(): Promise<any> {
    return this.makeRequest<any>('/dashboard/stats');
  }

  async getPendingApprovals(): Promise<PermissionGrant[]> {
    return this.makeRequest<PermissionGrant[]>('/dashboard/pending-approvals');
  }

  async getRecentActivity(): Promise<AuditLog[]> {
    return this.makeRequest<AuditLog[]>('/dashboard/recent-activity');
  }

  // Password Reset
  async requestPasswordReset(email: string): Promise<void> {
    await this.makeRequest<void>('/auth/password-reset-request', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.makeRequest<void>('/auth/password-reset', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    return this.makeRequest<{ status: string }>('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;