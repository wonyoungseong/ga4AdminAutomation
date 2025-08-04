'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { UserRole, PermissionGrant, AuditLog } from '@/types/auth';
import { apiClient } from '@/lib/api';
import {
  AdminStats,
  UserStats,
  PendingApprovals,
  RecentActivity,
  MyRequests,
  SystemHealth,
  WelcomeMessage,
} from '@/components/dashboard/dashboard-widgets';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

interface DashboardStats {
  admin: {
    totalUsers: number;
    activeUsers: number;
    pendingRequests: number;
    totalClients: number;
    totalServiceAccounts: number;
    totalPermissions: number;
  };
  user: {
    myRequests: number;
    approvedRequests: number;
    pendingRequests: number;
    rejectedRequests: number;
  };
  system: {
    status: 'healthy' | 'warning' | 'error';
    uptime: string;
    lastBackup: string;
    activeConnections: number;
  };
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<PermissionGrant[]>([]);
  const [recentActivity, setRecentActivity] = useState<AuditLog[]>([]);
  const [myRequests, setMyRequests] = useState<PermissionGrant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load data based on user role
        const promises: Promise<any>[] = [];

        // Always load recent activity
        promises.push(apiClient.getRecentActivity());

        // Role-specific data loading
        if (user.role === UserRole.SUPER_ADMIN || user.role === UserRole.ADMIN) {
          promises.push(
            apiClient.getDashboardStats(),
            apiClient.getPendingApprovals(),
          );
        }

        if (user.role === UserRole.REQUESTER || user.role === UserRole.GA_USER) {
          promises.push(
            apiClient.getPermissionGrants(1, 10, user.id)
          );
        }

        const results = await Promise.allSettled(promises);
        
        // Process results
        let activityIndex = 0;
        const activity = results[activityIndex].status === 'fulfilled' 
          ? results[activityIndex].value 
          : [];
        setRecentActivity(activity);

        if (user.role === UserRole.SUPER_ADMIN || user.role === UserRole.ADMIN) {
          const statsIndex = 1;
          const approvalsIndex = 2;
          
          if (results[statsIndex].status === 'fulfilled') {
            setStats({
              admin: results[statsIndex].value,
              user: {
                myRequests: 0,
                approvedRequests: 0,
                pendingRequests: 0,
                rejectedRequests: 0,
              },
              system: {
                status: 'healthy',
                uptime: '99.9%',
                lastBackup: '2 hours ago',
                activeConnections: 42,
              }
            });
          }
          
          if (results[approvalsIndex].status === 'fulfilled') {
            setPendingApprovals(results[approvalsIndex].value);
          }
        }

        if (user.role === UserRole.REQUESTER || user.role === UserRole.GA_USER) {
          const requestsIndex = 1;
          
          if (results[requestsIndex].status === 'fulfilled') {
            const requests = results[requestsIndex].value.items || [];
            setMyRequests(requests);
            
            // Calculate user stats
            const userStats = {
              myRequests: requests.length,
              approvedRequests: requests.filter((r: PermissionGrant) => r.status === 'approved').length,
              pendingRequests: requests.filter((r: PermissionGrant) => r.status === 'pending').length,
              rejectedRequests: requests.filter((r: PermissionGrant) => r.status === 'rejected').length,
            };
            
            setStats({
              admin: {
                totalUsers: 0,
                activeUsers: 0,
                pendingRequests: 0,
                totalClients: 0,
                totalServiceAccounts: 0,
                totalPermissions: 0,
              },
              user: userStats,
              system: {
                status: 'healthy',
                uptime: '99.9%',
                lastBackup: '2 hours ago',
                activeConnections: 42,
              }
            });
          }
        }

      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [user]);

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load dashboard data: {error}
          </AlertDescription>
        </Alert>
        <WelcomeMessage user={user} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">
          Welcome back! Here's what's happening with your GA4 permissions.
        </p>
      </div>

      {/* Welcome Message */}
      <WelcomeMessage user={user} />

      {/* Role-based Content */}
      {(user.role === UserRole.SUPER_ADMIN || user.role === UserRole.ADMIN) && (
        <>
          {/* Admin Stats */}
          {stats && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Overview</h2>
              <AdminStats stats={stats.admin} />
            </div>
          )}

          {/* Admin Widgets */}
          <div className="grid gap-6 md:grid-cols-2">
            <PendingApprovals requests={pendingApprovals} loading={loading} />
            <RecentActivity activities={recentActivity} loading={loading} />
          </div>

          {/* System Health (Super Admin only) */}
          {user.role === UserRole.SUPER_ADMIN && stats && (
            <SystemHealth health={stats.system} />
          )}
        </>
      )}

      {(user.role === UserRole.REQUESTER || user.role === UserRole.GA_USER) && (
        <>
          {/* User Stats */}
          {stats && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">My Permissions</h2>
              <UserStats stats={stats.user} />
            </div>
          )}

          {/* User Widgets */}
          <div className="grid gap-6 md:grid-cols-2">
            <MyRequests requests={myRequests} loading={loading} />
            <RecentActivity activities={recentActivity} loading={loading} />
          </div>
        </>
      )}

      {/* Additional Information Card */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
          <CardDescription>
            Tips and resources to help you make the most of the GA4 Admin system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {user.role === UserRole.SUPER_ADMIN && (
              <>
                <div className="space-y-2">
                  <h4 className="font-medium">User Management</h4>
                  <p className="text-sm text-muted-foreground">
                    Create and manage user accounts, assign roles, and monitor activity.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">System Settings</h4>
                  <p className="text-sm text-muted-foreground">
                    Configure system-wide settings, backup policies, and security options.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">Audit & Compliance</h4>
                  <p className="text-sm text-muted-foreground">
                    Review audit logs and generate compliance reports.
                  </p>
                </div>
              </>
            )}
            
            {user.role === UserRole.ADMIN && (
              <>
                <div className="space-y-2">
                  <h4 className="font-medium">Permission Approvals</h4>
                  <p className="text-sm text-muted-foreground">
                    Review and approve permission requests from users.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">Client Management</h4>
                  <p className="text-sm text-muted-foreground">
                    Manage client accounts and service account configurations.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">Activity Monitoring</h4>
                  <p className="text-sm text-muted-foreground">
                    Monitor system activity and user actions.
                  </p>
                </div>
              </>
            )}
            
            {(user.role === UserRole.REQUESTER || user.role === UserRole.GA_USER) && (
              <>
                <div className="space-y-2">
                  <h4 className="font-medium">Request Permissions</h4>
                  <p className="text-sm text-muted-foreground">
                    Submit new permission requests for GA4 properties.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">Track Status</h4>
                  <p className="text-sm text-muted-foreground">
                    Monitor the status of your permission requests.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">Manage Profile</h4>
                  <p className="text-sm text-muted-foreground">
                    Update your profile information and preferences.
                  </p>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}