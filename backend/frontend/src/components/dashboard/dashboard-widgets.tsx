'use client';

import React from 'react';
import Link from 'next/link';
import { 
  Users, 
  Shield, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  TrendingUp,
  Building2,
  Key,
  FileText,
  Activity,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useAuth } from '@/contexts/auth-context';
import { UserRole, PermissionGrant, AuditLog, User } from '@/types/auth';
import { formatRelativeTime, getStatusColor, getInitials, getRoleColor } from '@/lib/utils';
import { AdminGuard, RoleGuard, PermissionGuard } from '@/components/auth/permission-guard';

// Statistics Widget
interface StatsWidgetProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<any>;
  description?: string;
  href?: string;
}

export function StatsWidget({ 
  title, 
  value, 
  change, 
  changeType = 'neutral',
  icon: Icon, 
  description,
  href 
}: StatsWidgetProps) {
  const content = (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
            <TrendingUp className={`h-3 w-3 ${
              changeType === 'positive' ? 'text-green-500' : 
              changeType === 'negative' ? 'text-red-500' : 
              'text-gray-500'
            }`} />
            <span>{change}</span>
          </div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

// Admin Dashboard Stats
interface AdminStatsProps {
  stats: {
    totalUsers: number;
    activeUsers: number;
    pendingRequests: number;
    totalClients: number;
    totalServiceAccounts: number;
    totalPermissions: number;
  };
}

export function AdminStats({ stats }: AdminStatsProps) {
  return (
    <AdminGuard>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatsWidget
          title="Total Users"
          value={stats.totalUsers}
          icon={Users}
          description="Registered users"
          href="/dashboard/users"
        />
        <StatsWidget
          title="Active Users"
          value={stats.activeUsers}
          icon={Activity}
          description="Currently active"
          href="/dashboard/users?status=active"
        />
        <StatsWidget
          title="Pending Requests"
          value={stats.pendingRequests}
          icon={Clock}
          description="Awaiting approval"
          href="/dashboard/permissions/pending"
        />
        <StatsWidget
          title="Clients"
          value={stats.totalClients}
          icon={Building2}
          description="Registered clients"
          href="/dashboard/clients"
        />
        <StatsWidget
          title="Service Accounts"
          value={stats.totalServiceAccounts}
          icon={Key}
          description="Active accounts"
          href="/dashboard/service-accounts"
        />
        <StatsWidget
          title="Permissions"
          value={stats.totalPermissions}
          icon={Shield}
          description="Total granted"
          href="/dashboard/permissions"
        />
      </div>
    </AdminGuard>
  );
}

// User Dashboard Stats
interface UserStatsProps {
  stats: {
    myRequests: number;
    approvedRequests: number;
    pendingRequests: number;
    rejectedRequests: number;
  };
}

export function UserStats({ stats }: UserStatsProps) {
  return (
    <RoleGuard roles={[UserRole.REQUESTER, UserRole.GA_USER]}>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsWidget
          title="Total Requests"
          value={stats.myRequests}
          icon={Shield}
          description="All my requests"
          href="/dashboard/permissions/my-requests"
        />
        <StatsWidget
          title="Approved"
          value={stats.approvedRequests}
          icon={CheckCircle}
          description="Approved requests"
          href="/dashboard/permissions/my-requests?status=approved"
        />
        <StatsWidget
          title="Pending"
          value={stats.pendingRequests}
          icon={Clock}
          description="Awaiting approval"
          href="/dashboard/permissions/my-requests?status=pending"
        />
        <StatsWidget
          title="Rejected"
          value={stats.rejectedRequests}
          icon={AlertCircle}
          description="Rejected requests"
          href="/dashboard/permissions/my-requests?status=rejected"
        />
      </div>
    </RoleGuard>
  );
}

// Pending Approvals Widget
interface PendingApprovalsProps {
  requests: PermissionGrant[];
  loading?: boolean;
}

export function PendingApprovals({ requests, loading }: PendingApprovalsProps) {
  return (
    <PermissionGuard requiredPermissions="permissions.approve">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Pending Approvals</span>
            <Badge variant="secondary">{requests.length}</Badge>
          </CardTitle>
          <CardDescription>
            Permission requests awaiting your approval
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : requests.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No pending approvals
            </p>
          ) : (
            <div className="space-y-3">
              {requests.slice(0, 5).map((request) => (
                <div key={request.id} className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {request.target_email}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {request.ga_property_id} • {request.permission_level}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(request.status)}>
                      {request.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(request.created_at)}
                    </span>
                  </div>
                </div>
              ))}
              {requests.length > 5 && (
                <Link href="/dashboard/permissions/pending">
                  <Button variant="outline" size="sm" className="w-full">
                    View All ({requests.length})
                  </Button>
                </Link>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </PermissionGuard>
  );
}

// Recent Activity Widget
interface RecentActivityProps {
  activities: AuditLog[];
  loading?: boolean;
}

export function RecentActivity({ activities, loading }: RecentActivityProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>
          Latest actions in the system
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : activities.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No recent activity
          </p>
        ) : (
          <div className="space-y-3">
            {activities.slice(0, 10).map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm">
                    <span className="font-medium">{activity.action}</span>
                    {' '}on{' '}
                    <span className="font-medium">{activity.resource_type}</span>
                    {activity.resource_id && (
                      <>
                        {' '}
                        <span className="text-muted-foreground">
                          #{activity.resource_id}
                        </span>
                      </>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatRelativeTime(activity.created_at)}
                  </p>
                </div>
              </div>
            ))}
            <PermissionGuard requiredPermissions="audit_logs.read">
              <Link href="/dashboard/audit-logs">
                <Button variant="outline" size="sm" className="w-full">
                  View All Activity
                </Button>
              </Link>
            </PermissionGuard>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// My Requests Widget (for requesters)
interface MyRequestsProps {
  requests: PermissionGrant[];
  loading?: boolean;
}

export function MyRequests({ requests, loading }: MyRequestsProps) {
  return (
    <RoleGuard roles={[UserRole.REQUESTER, UserRole.GA_USER]}>
      <Card>
        <CardHeader>
          <CardTitle>My Recent Requests</CardTitle>
          <CardDescription>
            Your latest permission requests
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : requests.length === 0 ? (
            <div className="text-center py-4">
              <Shield className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground mb-2">
                No requests yet
              </p>
              <Link href="/dashboard/permissions/new">
                <Button size="sm">Create First Request</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {requests.slice(0, 5).map((request) => (
                <div key={request.id} className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {request.target_email}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {request.ga_property_id} • {request.permission_level}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(request.status)}>
                      {request.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(request.created_at)}
                    </span>
                  </div>
                </div>
              ))}
              <Link href="/dashboard/permissions/my-requests">
                <Button variant="outline" size="sm" className="w-full">
                  View All Requests
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </RoleGuard>
  );
}

// System Health Widget (Super Admin only)
interface SystemHealthProps {
  health: {
    status: 'healthy' | 'warning' | 'error';
    uptime: string;
    lastBackup: string;
    activeConnections: number;
  };
}

export function SystemHealth({ health }: SystemHealthProps) {
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <RoleGuard roles={UserRole.SUPER_ADMIN}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>System Health</span>
            <Badge className={getHealthColor(health.status)}>
              {health.status.toUpperCase()}
            </Badge>
          </CardTitle>
          <CardDescription>
            System status and metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Uptime</span>
              <span>{health.uptime}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Last Backup</span>
              <span>{health.lastBackup}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Active Connections</span>
              <span>{health.activeConnections}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </RoleGuard>
  );
}

// Role-based Welcome Message
interface WelcomeMessageProps {
  user: User;
}

export function WelcomeMessage({ user }: WelcomeMessageProps) {
  const getMessage = (role: UserRole) => {
    switch (role) {
      case UserRole.SUPER_ADMIN:
        return {
          title: `Welcome back, ${user.name}!`,
          description: "You have full system access. Monitor users, manage settings, and oversee all operations.",
          actions: [
            { label: "Manage Users", href: "/dashboard/users" },
            { label: "System Settings", href: "/dashboard/settings" },
            { label: "View Audit Logs", href: "/dashboard/audit-logs" },
          ]
        };
      case UserRole.ADMIN:
        return {
          title: `Hello, ${user.name}!`,
          description: "Manage clients, approve permissions, and monitor system activity.",
          actions: [
            { label: "Pending Approvals", href: "/dashboard/permissions/pending" },
            { label: "Manage Clients", href: "/dashboard/clients" },
            { label: "View Activity", href: "/dashboard/audit-logs" },
          ]
        };
      case UserRole.REQUESTER:
        return {
          title: `Welcome, ${user.name}!`,
          description: "Create permission requests and track their status.",
          actions: [
            { label: "New Request", href: "/dashboard/permissions/new" },
            { label: "My Requests", href: "/dashboard/permissions/my-requests" },
            { label: "Update Profile", href: "/dashboard/profile" },
          ]
        };
      case UserRole.GA_USER:
        return {
          title: `Hi, ${user.name}!`,
          description: "View your permissions and manage your profile.",
          actions: [
            { label: "My Permissions", href: "/dashboard/permissions/my-requests" },
            { label: "Update Profile", href: "/dashboard/profile" },
          ]
        };
      default:
        return {
          title: `Welcome, ${user.name}!`,
          description: "Access your dashboard and manage your account.",
          actions: [
            { label: "View Profile", href: "/dashboard/profile" },
          ]
        };
    }
  };

  const message = getMessage(user.role);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{message.title}</CardTitle>
        <CardDescription>{message.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {message.actions.map((action) => (
            <Link key={action.href} href={action.href}>
              <Button variant="outline" size="sm">
                {action.label}
              </Button>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}