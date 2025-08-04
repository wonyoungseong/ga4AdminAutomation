'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { 
  User, 
  AuthToken, 
  LoginRequest, 
  RegisterRequest, 
  AuthContextType,
  UserRole,
  RolePermissions
} from '@/types/auth';
import { apiClient } from '@/lib/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem('auth_token');
        const storedUser = localStorage.getItem('auth_user');

        if (storedToken && storedUser) {
          setToken(storedToken);
          apiClient.setToken(storedToken);
          
          try {
            // Verify token is still valid by fetching current user
            const currentUser = await apiClient.getCurrentUser();
            setUser(currentUser);
            localStorage.setItem('auth_user', JSON.stringify(currentUser));
          } catch (error) {
            // Token is invalid, clear auth state
            console.error('Token validation failed:', error);
            await logout();
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      setIsLoading(true);
      const authToken = await apiClient.login(credentials);
      
      // Set token in API client
      apiClient.setToken(authToken.access_token);
      
      // Get user data
      const userData = await apiClient.getCurrentUser();
      
      // Update state
      setToken(authToken.access_token);
      setUser(userData);
      
      // Store in localStorage
      localStorage.setItem('auth_token', authToken.access_token);
      localStorage.setItem('auth_user', JSON.stringify(userData));
      localStorage.setItem('refresh_token', authToken.refresh_token);
      
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      setIsLoading(true);
      await apiClient.register(userData);
      
      // After successful registration, log the user in
      await login({
        email: userData.email,
        password: userData.password,
      });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Call logout endpoint if we have a token
      if (token) {
        await apiClient.logout();
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Clear local state regardless of API call result
      setUser(null);
      setToken(null);
      apiClient.setToken(null);
      
      // Clear localStorage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('refresh_token');
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      if (!refreshTokenValue) {
        throw new Error('No refresh token available');
      }

      const authToken = await apiClient.refreshToken();
      
      // Update token
      setToken(authToken.access_token);
      apiClient.setToken(authToken.access_token);
      
      // Store new tokens
      localStorage.setItem('auth_token', authToken.access_token);
      localStorage.setItem('refresh_token', authToken.refresh_token);
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      throw error;
    }
  };

  const hasRole = (roles: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    
    const requiredRoles = Array.isArray(roles) ? roles : [roles];
    return requiredRoles.includes(user.role);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    const userPermissions = RolePermissions[user.role] || [];
    return userPermissions.includes(permission);
  };

  // Auto-refresh token before it expires
  useEffect(() => {
    if (!token) return;

    const tokenData = JSON.parse(atob(token.split('.')[1]));
    const expirationTime = tokenData.exp * 1000; // Convert to milliseconds
    const currentTime = Date.now();
    const timeUntilExpiry = expirationTime - currentTime;
    
    // Refresh token 5 minutes before expiry
    const refreshTime = timeUntilExpiry - (5 * 60 * 1000);
    
    if (refreshTime > 0) {
      const timeoutId = setTimeout(() => {
        refreshToken().catch(console.error);
      }, refreshTime);
      
      return () => clearTimeout(timeoutId);
    }
  }, [token]);

  const contextValue: AuthContextType = {
    user,
    token,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
    hasRole,
    hasPermission,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Higher-order component for protecting routes
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { user, isLoading } = useAuth();
    
    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      );
    }
    
    if (!user) {
      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login';
      }
      return null;
    }
    
    return <Component {...props} />;
  };
}

// Hook for role-based access control
export function useRoleAccess(requiredRoles: UserRole | UserRole[]) {
  const { user, hasRole } = useAuth();
  
  return {
    hasAccess: hasRole(requiredRoles),
    user,
    userRole: user?.role,
  };
}

// Hook for permission-based access control
export function usePermissionAccess(requiredPermissions: string | string[]) {
  const { user, hasPermission } = useAuth();
  
  const permissions = Array.isArray(requiredPermissions) 
    ? requiredPermissions 
    : [requiredPermissions];
    
  const hasAccess = permissions.some(permission => hasPermission(permission));
  
  return {
    hasAccess,
    user,
    userRole: user?.role,
  };
}