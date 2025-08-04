'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { PermissionGrant, UserRole, PermissionStatus, PaginatedResponse } from '@/types/auth';
import { apiClient } from '@/lib/api';
import { PermissionGuard } from '@/components/auth/permission-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Shield, 
  Plus, 
  MoreHorizontal, 
  Check, 
  X, 
  Eye, 
  AlertCircle,
  Search,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { 
  formatDate, 
  formatRelativeTime,
  getStatusColor, 
  getPermissionLevelColor,
  snakeToTitle 
} from '@/lib/utils';

export default function PermissionsPage() {
  const { user: currentUser } = useAuth();
  const [permissions, setPermissions] = useState<PermissionGrant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<PermissionStatus | 'all'>('all');

  const loadPermissions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load permissions based on user role
      let response: PaginatedResponse<PermissionGrant>;
      
      if (currentUser?.role === UserRole.SUPER_ADMIN || currentUser?.role === UserRole.ADMIN) {
        // Admins can see all permissions
        response = await apiClient.getPermissionGrants(page);
      } else {
        // Regular users can only see their own permissions
        response = await apiClient.getPermissionGrants(page, 20, currentUser?.id);
      }
      
      setPermissions(response.items);
      setTotalPages(Math.ceil(response.total / response.size));
    } catch (err) {
      console.error('Failed to load permissions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load permissions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadPermissions();
    }
  }, [page, currentUser]);

  const handleApprove = async (permissionId: number) => {
    try {
      await apiClient.approvePermissionGrant(permissionId);
      await loadPermissions(); // Reload the list
    } catch (err) {
      console.error('Failed to approve permission:', err);
      setError(err instanceof Error ? err.message : 'Failed to approve permission');
    }
  };

  const handleReject = async (permissionId: number) => {
    const reason = prompt('Please provide a reason for rejection (optional):');
    
    try {
      await apiClient.rejectPermissionGrant(permissionId, reason || undefined);
      await loadPermissions(); // Reload the list
    } catch (err) {
      console.error('Failed to reject permission:', err);
      setError(err instanceof Error ? err.message : 'Failed to reject permission');
    }
  };

  const handleDelete = async (permissionId: number) => {
    if (!confirm('Are you sure you want to delete this permission request? This action cannot be undone.')) {
      return;
    }

    try {
      await apiClient.deletePermissionGrant(permissionId);
      await loadPermissions(); // Reload the list
    } catch (err) {
      console.error('Failed to delete permission:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete permission');
    }
  };

  // Filter permissions based on search and filters
  const filteredPermissions = permissions.filter(permission => {
    const matchesSearch = permission.target_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         permission.ga_property_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         permission.reason?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         permission.notes?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || permission.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: PermissionStatus) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'approved': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'expired': return <AlertCircle className="h-4 w-4 text-gray-500" />;
      case 'revoked': return <X className="h-4 w-4 text-red-500" />;
      default: return <Shield className="h-4 w-4 text-gray-500" />;
    }
  };

  const canManagePermissions = currentUser?.role === UserRole.SUPER_ADMIN || currentUser?.role === UserRole.ADMIN;

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <PermissionGuard requiredPermissions={['permissions.read', 'permissions.read_own']}>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {canManagePermissions ? 'All Permissions' : 'My Permissions'}
            </h1>
            <p className="text-gray-600">
              {canManagePermissions 
                ? 'Manage and approve GA4 permission requests'
                : 'View and track your GA4 permission requests'
              }
            </p>
          </div>
          <PermissionGuard requiredPermissions="permissions.create">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Request
            </Button>
          </PermissionGuard>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-yellow-500" />
                <div>
                  <p className="text-sm font-medium">Pending</p>
                  <p className="text-2xl font-bold">
                    {filteredPermissions.filter(p => p.status === 'pending').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <div>
                  <p className="text-sm font-medium">Approved</p>
                  <p className="text-2xl font-bold">
                    {filteredPermissions.filter(p => p.status === 'approved').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <XCircle className="h-4 w-4 text-red-500" />
                <div>
                  <p className="text-sm font-medium">Rejected</p>
                  <p className="text-2xl font-bold">
                    {filteredPermissions.filter(p => p.status === 'rejected').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Shield className="h-4 w-4 text-blue-500" />
                <div>
                  <p className="text-sm font-medium">Total</p>
                  <p className="text-2xl font-bold">{filteredPermissions.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search permissions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as PermissionStatus | 'all')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="expired">Expired</option>
                <option value="revoked">Revoked</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Permissions List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center">
                <Shield className="mr-2 h-5 w-5" />
                Permission Requests ({filteredPermissions.length})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : filteredPermissions.length === 0 ? (
              <div className="text-center py-8">
                <Shield className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No permissions found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || statusFilter !== 'all'
                    ? 'Try adjusting your search or filters.'
                    : 'Get started by creating your first permission request.'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredPermissions.map((permission) => (
                  <div
                    key={permission.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          {getStatusIcon(permission.status)}
                          <h3 className="text-sm font-medium text-gray-900">
                            {permission.target_email}
                          </h3>
                          <Badge className={getStatusColor(permission.status)}>
                            {snakeToTitle(permission.status)}
                          </Badge>
                          <Badge className={getPermissionLevelColor(permission.permission_level)}>
                            {snakeToTitle(permission.permission_level)}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                          <div>
                            <p><span className="font-medium">Property ID:</span> {permission.ga_property_id}</p>
                            <p><span className="font-medium">Requested:</span> {formatRelativeTime(permission.created_at)}</p>
                          </div>
                          <div>
                            {permission.expires_at && (
                              <p><span className="font-medium">Expires:</span> {formatDate(permission.expires_at)}</p>
                            )}
                            {permission.approved_at && (
                              <p><span className="font-medium">Approved:</span> {formatDate(permission.approved_at)}</p>
                            )}
                          </div>
                        </div>
                        
                        {permission.reason && (
                          <div className="mt-2">
                            <p className="text-sm text-gray-600">
                              <span className="font-medium">Reason:</span> {permission.reason}
                            </p>
                          </div>
                        )}
                        
                        {permission.notes && (
                          <div className="mt-2">
                            <p className="text-sm text-gray-600">
                              <span className="font-medium">Notes:</span> {permission.notes}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center space-x-2">
                        {/* Approval Actions */}
                        <PermissionGuard requiredPermissions="permissions.approve">
                          {permission.status === 'pending' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleApprove(permission.id)}
                                className="text-green-600 hover:bg-green-50"
                              >
                                <Check className="h-4 w-4 mr-1" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReject(permission.id)}
                                className="text-red-600 hover:bg-red-50"
                              >
                                <X className="h-4 w-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                        </PermissionGuard>

                        {/* More Actions Menu */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            
                            <DropdownMenuItem>
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            
                            <PermissionGuard requiredPermissions="permissions.update">
                              <DropdownMenuItem>
                                Edit Request
                              </DropdownMenuItem>
                            </PermissionGuard>
                            
                            <PermissionGuard requiredPermissions="permissions.delete">
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleDelete(permission.id)}
                                className="text-red-600"
                              >
                                Delete Request
                              </DropdownMenuItem>
                            </PermissionGuard>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center space-x-2">
            <Button
              variant="outline"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            
            <div className="flex items-center space-x-1">
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <Button
                    key={pageNum}
                    variant={page === pageNum ? "default" : "outline"}
                    onClick={() => setPage(pageNum)}
                    className="w-10 h-10 p-0"
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>
            
            <Button
              variant="outline"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </PermissionGuard>
  );
}