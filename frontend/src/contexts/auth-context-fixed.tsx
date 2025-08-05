"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useClientOnly } from '@/hooks/use-client-only';
import { typeSafeApiClient, ApiClientError } from '@/lib/api-client';
import { User } from '@/types/api';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  isRefreshing: boolean;
  token: string | null;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();
  const isClient = useClientOnly();

  // Track authentication state changes across tabs
  useEffect(() => {
    if (!isClient) {
      setIsLoading(false);
      return;
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'auth_token') {
        if (e.newValue) {
          setToken(e.newValue);
          // Don't fetch user info here as it might be handled by the tab that set the token
        } else {
          // Token was removed, clear user state
          setUser(null);
          setToken(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [isClient]);

  // Initialize authentication state
  useEffect(() => {
    if (!isClient) {
      setIsLoading(false);
      return;
    }
    
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');
      if (storedToken) {
        setToken(storedToken);
        
        // Check if token is expired before making API call
        const isExpired = isTokenExpired(storedToken);
        if (isExpired) {
          console.log('Token expired, attempting refresh...');
          const refreshSuccess = await refreshToken();
          if (!refreshSuccess) {
            console.log('Token refresh failed, clearing auth state');
            clearAuthState();
          }
        } else {
          // Token is valid, fetch user info
          await fetchUserInfo(storedToken);
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, [isClient]);

  const isTokenExpired = (tokenToCheck: string): boolean => {
    try {
      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      const expiry = payload.exp * 1000;
      const now = Date.now();
      // Add 60 second buffer to account for network delays
      return now >= (expiry - 60000);
    } catch (error) {
      console.warn('Failed to parse token expiry:', error);
      return true; // Assume expired if can't parse
    }
  };

  const clearAuthState = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expiry');
    setToken(null);
    setUser(null);
  }, []);

  const fetchUserInfo = async (authToken: string): Promise<boolean> => {
    try {
      const userData = await typeSafeApiClient.getCurrentUser();
      setUser(userData);
      return true;
    } catch (error) {
      console.error('사용자 정보 조회 실패:', error);
      if (error instanceof ApiClientError && error.statusCode === 401) {
        // Token is invalid, try refresh
        const refreshSuccess = await refreshToken();
        if (refreshSuccess) {
          return true; // User info will be fetched after successful refresh
        } else {
          clearAuthState();
          return false;
        }
      }
      // Non-auth error, keep trying
      return false;
    }
  };

  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (isRefreshing) {
      // Already refreshing, wait for it to complete
      return new Promise((resolve) => {
        const checkRefreshComplete = () => {
          if (!isRefreshing) {
            resolve(!!user);
          } else {
            setTimeout(checkRefreshComplete, 100);
          }
        };
        checkRefreshComplete();
      });
    }

    setIsRefreshing(true);
    try {
      const newToken = await typeSafeApiClient.refreshAuthToken();
      if (newToken) {
        setToken(newToken);
        // Fetch user info with new token
        const userSuccess = await fetchUserInfo(newToken);
        if (userSuccess) {
          console.log('Token refreshed successfully');
          return true;
        }
      }
      
      console.log('Token refresh failed');
      clearAuthState();
      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      clearAuthState();
      return false;
    } finally {
      setIsRefreshing(false);
    }
  }, [isRefreshing, user, clearAuthState]);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const data = await typeSafeApiClient.login(email, password);
      const { access_token, user: userData } = data;
      
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return true;
    } catch (error) {
      console.error('로그인 중 오류 발생:', error);
      if (error instanceof ApiClientError) {
        console.error('로그인 실패:', error.details || error.message);
      }
      return false;
    }
  };

  const logout = useCallback(() => {
    clearAuthState();
    router.push('/login');
  }, [clearAuthState, router]);

  const contextValue: AuthContextType = {
    user,
    login,
    logout,
    isLoading,
    isRefreshing,
    token,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}