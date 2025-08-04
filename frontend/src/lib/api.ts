const API_BASE_URL = 'http://localhost:8001';

export class ApiClient {
  private getAuthHeader(): { Authorization?: string } {
    const token = localStorage.getItem('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeader(),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // 인증 관련
  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
      }),
    });

    if (!response.ok) {
      throw new Error('로그인 실패');
    }

    return response.json();
  }

  async getCurrentUser() {
    return this.request('/api/auth/me');
  }

  // 대시보드 통계
  async getDashboardStats() {
    return this.request('/api/dashboard/stats');
  }

  // 사용자 관리
  async getUsers(page: number = 1, limit: number = 10) {
    return this.request(`/api/users?page=${page}&limit=${limit}`);
  }

  async getUserById(id: number) {
    return this.request(`/api/users/${id}`);
  }

  async createUser(userData: any) {
    return this.request('/api/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(id: number, userData: any) {
    return this.request(`/api/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(id: number) {
    return this.request(`/api/users/${id}`, {
      method: 'DELETE',
    });
  }

  // 권한 관리
  async getPermissions(page: number = 1, limit: number = 10) {
    return this.request(`/api/permissions`);
  }

  async getPermissionById(id: number) {
    return this.request(`/api/permissions/${id}`);
  }

  async createPermission(permissionData: any) {
    return this.request('/api/permissions', {
      method: 'POST',
      body: JSON.stringify(permissionData),
    });
  }

  async updatePermission(id: number, permissionData: any) {
    return this.request(`/api/permissions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(permissionData),
    });
  }

  async deletePermission(id: number) {
    return this.request(`/api/permissions/${id}`, {
      method: 'DELETE',
    });
  }

  // 클라이언트 관리
  async getClients(page: number = 1, limit: number = 10) {
    return this.request(`/api/clients?page=${page}&limit=${limit}`);
  }

  async getClientById(id: number) {
    return this.request(`/api/clients/${id}`);
  }

  async createClient(clientData: any) {
    return this.request('/api/clients', {
      method: 'POST',
      body: JSON.stringify(clientData),
    });
  }

  async updateClient(id: number, clientData: any) {
    return this.request(`/api/clients/${id}`, {
      method: 'PUT',
      body: JSON.stringify(clientData),
    });
  }

  async deleteClient(id: number) {
    return this.request(`/api/clients/${id}`, {
      method: 'DELETE',
    });
  }

  // 감사 로그
  async getAuditLogs(page: number = 1, limit: number = 50, filters?: any) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    // 필터 추가
    if (filters) {
      if (filters.action) params.append('action', filters.action);
      if (filters.user_email) params.append('user_email', filters.user_email);
      if (filters.target_type) params.append('target_type', filters.target_type);
      if (filters.status) params.append('status', filters.status);
    }
    
    return this.request(`/api/audit-logs?${params}`);
  }

  async getAuditLogById(id: number) {
    return this.request(`/api/audit-logs/${id}`);
  }

  async getAuditLogStats() {
    return this.request('/api/audit-logs/stats');
  }

  // Service Account API
  async getServiceAccounts(page: number = 1, limit: number = 20, client_id?: number) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (client_id) params.append('client_id', client_id.toString());
    return this.request(`/api/service-accounts?${params}`);
  }

  async getServiceAccountById(id: number) {
    return this.request(`/api/service-accounts/${id}`);
  }

  async createServiceAccount(serviceAccountData: FormData) {
    const url = `${API_BASE_URL}/api/service-accounts`;
    const headers = {
      ...this.getAuthHeader(),
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: serviceAccountData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async updateServiceAccount(id: number, serviceAccountData: any) {
    return this.request(`/api/service-accounts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(serviceAccountData),
    });
  }

  async deleteServiceAccount(id: number) {
    return this.request(`/api/service-accounts/${id}`, {
      method: 'DELETE',
    });
  }

  async discoverGA4Properties(serviceAccountId: number) {
    return this.request(`/api/service-accounts/${serviceAccountId}/discover-properties`, {
      method: 'POST',
    });
  }

  async syncServiceAccountPermissions(serviceAccountId: number) {
    return this.request(`/api/service-accounts/${serviceAccountId}/sync-permissions`, {
      method: 'POST',
    });
  }

  async testServiceAccountHealth(serviceAccountId: number) {
    return this.request(`/api/service-accounts/${serviceAccountId}/health`);
  }

  // GA4 Properties API
  async getGA4PropertiesManagement(page: number = 1, limit: number = 20, service_account_id?: number, client_id?: number) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (service_account_id) params.append('service_account_id', service_account_id.toString());
    if (client_id) params.append('client_id', client_id.toString());
    return this.request(`/api/ga4-properties?${params}`);
  }

  async getGA4PropertyById(id: number) {
    return this.request(`/api/ga4-properties/${id}`);
  }

  async updateGA4Property(id: number, propertyData: any) {
    return this.request(`/api/ga4-properties/${id}`, {
      method: 'PUT',
      body: JSON.stringify(propertyData),
    });
  }

  async deleteGA4Property(id: number) {
    return this.request(`/api/ga4-properties/${id}`, {
      method: 'DELETE',
    });
  }

  async assignPropertyToClient(propertyId: number, clientId: number) {
    return this.request(`/api/ga4-properties/${propertyId}/assign-client`, {
      method: 'POST',
      body: JSON.stringify({ client_id: clientId }),
    });
  }

  async unassignPropertyFromClient(propertyId: number) {
    return this.request(`/api/ga4-properties/${propertyId}/unassign-client`, {
      method: 'POST',
    });
  }

  async validatePropertyAccess(propertyId: number) {
    return this.request(`/api/ga4-properties/${propertyId}/validate-access`);
  }

  // GA4 API 관련 (Legacy)
  async getGA4Accounts() {
    return this.request('/api/ga4/accounts');
  }

  async getGA4Properties(accountId?: string) {
    const params = accountId ? `?account_id=${accountId}` : '';
    return this.request(`/api/ga4/properties${params}`);
  }

  async getPropertyPermissions(propertyId: string) {
    return this.request(`/api/ga4/properties/${propertyId}/permissions`);
  }

  async grantPropertyPermission(propertyId: string, userEmail: string, permissionType: string) {
    return this.request(`/api/ga4/properties/${propertyId}/permissions`, {
      method: 'POST',
      body: JSON.stringify({
        user_email: userEmail,
        permission_type: permissionType
      }),
    });
  }

  async revokePropertyPermission(propertyId: string, bindingName: string) {
    return this.request(`/api/ga4/properties/${propertyId}/permissions/${bindingName}`, {
      method: 'DELETE',
    });
  }

  async updatePropertyPermission(propertyId: string, bindingName: string, permissionType: string) {
    return this.request(`/api/ga4/properties/${propertyId}/permissions/${bindingName}`, {
      method: 'PUT',
      body: JSON.stringify({
        permission_type: permissionType
      }),
    });
  }
}

export const apiClient = new ApiClient();