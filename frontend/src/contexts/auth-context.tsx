"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useClientOnly } from '@/hooks/use-client-only';
import { typeSafeApiClient, ApiClientError } from '@/lib/api-client';
import { User } from '@/types/api';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  isInitialized: boolean;
  isRefreshing: boolean;
  token: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();
  const isClient = useClientOnly();

  useEffect(() => {
    let isMounted = true;
    
    console.log('[AuthContext] Initial setup - isClient:', isClient);
    if (!isClient) {
      console.log('[AuthContext] Not client-side yet, waiting...');
      return;
    }
    
    const initializeAuth = async () => {
      try {
        // Client-side only localStorage access
        const storedToken = localStorage.getItem('auth_token');
        const storedRefreshToken = localStorage.getItem('refresh_token');
        console.log('[AuthContext] Checking stored tokens:');
        console.log('  - Access token:', storedToken ? storedToken.substring(0, 20) + '...' : 'none');
        console.log('  - Refresh token:', storedRefreshToken ? storedRefreshToken.substring(0, 20) + '...' : 'none');
        
        if (storedToken && isMounted) {
          setToken(storedToken);
          // Always try to get user info, let fetchUserInfo handle token validation
          await fetchUserInfo(storedToken);
        } else {
          console.log('[AuthContext] No stored token found, setting loading to false');
          if (isMounted) {
            setIsLoading(false);
            setIsInitialized(true);
          }
        }
      } catch (error) {
        console.error('[AuthContext] Error during initialization:', error);
        if (isMounted) {
          setIsLoading(false);
          setIsInitialized(true);
        }
      }
    };

    initializeAuth();

    // Listen for storage changes across tabs
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'auth_token') {
        if (e.newValue && isMounted) {
          setToken(e.newValue);
          fetchUserInfo(e.newValue);
        } else if (isMounted) {
          setToken(null);
          setUser(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      isMounted = false;
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [isClient]);

  const tryRefreshToken = async () => {
    if (isRefreshing) {
      console.log('[AuthContext] Token refresh already in progress, waiting...');
      return;
    }

    setIsRefreshing(true);
    try {
      console.log('[AuthContext] Attempting token refresh...');
      const newToken = await typeSafeApiClient.refreshAuthToken();
      if (newToken) {
        console.log('[AuthContext] Token refresh successful');
        setToken(newToken);
        // Store the new token in localStorage
        localStorage.setItem('auth_token', newToken);
        // Fetch user info with new token
        const userData = await typeSafeApiClient.getCurrentUser();
        setUser(userData);
        setIsLoading(false);
        setIsInitialized(true);
      } else {
        console.log('[AuthContext] Token refresh failed - no new token received');
        // Refresh failed, clear tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        setToken(null);
        setUser(null);
        setIsLoading(false);
        setIsInitialized(true);
      }
    } catch (error) {
      console.error('[AuthContext] 토큰 갱신 실패:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setUser(null);
      setIsLoading(false);
      setIsInitialized(true);
    } finally {
      setIsRefreshing(false);
    }
  };

  const fetchUserInfo = async (authToken: string) => {
    console.log('[AuthContext] Fetching user info with token:', authToken.substring(0, 20) + '...');
    try {
      const userData = await typeSafeApiClient.getCurrentUser();
      console.log('[AuthContext] User info fetched successfully:', userData.name, userData.email);
      setUser(userData);
      setIsLoading(false);
      setIsInitialized(true);
    } catch (error) {
      console.error('[AuthContext] 사용자 정보 조회 실패:', error);
      if (error instanceof ApiClientError && error.statusCode === 401) {
        // Token is invalid/expired, try to refresh
        console.log('[AuthContext] Token expired (401), attempting refresh...');
        await tryRefreshToken();
        return;
      }
      // For other errors, still set loading to false
      console.error('[AuthContext] Non-401 error, setting initialized state');
      setIsLoading(false);
      setIsInitialized(true);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const data = await typeSafeApiClient.login(email, password);
      const { access_token, user } = data;
      
      localStorage.setItem('auth_token', access_token);
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      setToken(access_token);
      setUser(user);
      setIsLoading(false);
      setIsInitialized(true);
      
      return true;
    } catch (error) {
      console.error('로그인 중 오류 발생:', error);
      if (error instanceof ApiClientError) {
        console.error('로그인 실패:', error.details || error.message);
      }
      setIsLoading(false);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
    setIsInitialized(true);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading, isInitialized, isRefreshing, token }}>
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