"use client";

import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function AuthDebug() {
  const { user, isLoading, isInitialized, isRefreshing, token } = useAuth();

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Card className="fixed bottom-4 right-4 w-80 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Auth Debug</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <div className="flex justify-between items-center">
          <span>Loading:</span>
          <Badge variant={isLoading ? "destructive" : "default"}>
            {isLoading ? "Yes" : "No"}
          </Badge>
        </div>
        <div className="flex justify-between items-center">
          <span>Initialized:</span>
          <Badge variant={isInitialized ? "default" : "secondary"}>
            {isInitialized ? "Yes" : "No"}
          </Badge>
        </div>
        <div className="flex justify-between items-center">
          <span>Refreshing:</span>
          <Badge variant={isRefreshing ? "destructive" : "default"}>
            {isRefreshing ? "Yes" : "No"}
          </Badge>
        </div>
        <div className="flex justify-between items-center">
          <span>User:</span>
          <Badge variant={user ? "default" : "secondary"}>
            {user ? user.email : "None"}
          </Badge>
        </div>
        <div className="flex justify-between items-center">
          <span>Token:</span>
          <Badge variant={token ? "default" : "secondary"}>
            {token ? `${token.substring(0, 10)}...` : "None"}
          </Badge>
        </div>
        <div className="text-xs text-muted-foreground">
          <div>Local Token: {typeof window !== 'undefined' ? (localStorage.getItem('auth_token') ? 'Present' : 'None') : 'SSR'}</div>
          <div>Refresh Token: {typeof window !== 'undefined' ? (localStorage.getItem('refresh_token') ? 'Present' : 'None') : 'SSR'}</div>
        </div>
      </CardContent>
    </Card>
  );
}