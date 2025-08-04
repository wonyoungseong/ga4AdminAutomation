'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { User, UserRole, UserStatus, PaginatedResponse } from '@/types/auth';
import { apiClient } from '@/lib/api';
import { AdminGuard } from '@/components/auth/permission-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
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
  Users, 
  UserPlus, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  Shield, 
  AlertCircle,
  Search,
  Filter,
} from 'lucide-react';
import { formatDate, getInitials, getRoleColor, getStatusColor, snakeToTitle } from '@/lib/utils';

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<UserStatus | 'all'>('all');

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response: PaginatedResponse<User> = await apiClient.getUsers(page);
      setUsers(response.items);
      setTotalPages(Math.ceil(response.total / response.size));
    } catch (err) {
      console.error('Failed to load users:', err);
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [page]);

  const handleRoleChange = async (userId: number, newRole: UserRole) => {
    try {
      await apiClient.updateUser(userId, { role: newRole });
      await loadUsers(); // Reload the list
    } catch (err) {
      console.error('Failed to update user role:', err);
      setError(err instanceof Error ? err.message : 'Failed to update user role');
    }
  };

  const handleStatusChange = async (userId: number, newStatus: UserStatus) => {
    try {
      await apiClient.updateUser(userId, { status: newStatus });
      await loadUsers(); // Reload the list
    } catch (err) {
      console.error('Failed to update user status:', err);
      setError(err instanceof Error ? err.message : 'Failed to update user status');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      await apiClient.deleteUser(userId);
      await loadUsers(); // Reload the list
    } catch (err) {
      console.error('Failed to delete user:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };

  // Filter users based on search and filters
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (user.company?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
    
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <AdminGuard>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Users</h1>
            <p className="text-gray-600">
              Manage user accounts and permissions
            </p>
          </div>
          <Button>
            <UserPlus className="mr-2 h-4 w-4" />
            Add User
          </Button>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

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
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Role Filter */}
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value as UserRole | 'all')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="all">All Roles</option>
                <option value={UserRole.SUPER_ADMIN}>Super Admin</option>
                <option value={UserRole.ADMIN}>Admin</option>
                <option value={UserRole.REQUESTER}>Requester</option>
                <option value={UserRole.GA_USER}>GA User</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as UserStatus | 'all')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value={UserStatus.ACTIVE}>Active</option>
                <option value={UserStatus.INACTIVE}>Inactive</option>
                <option value={UserStatus.SUSPENDED}>Suspended</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Users List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center">
                <Users className="mr-2 h-5 w-5" />
                Users ({filteredUsers.length})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-center space-x-4">
                      <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="text-center py-8">
                <Users className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || roleFilter !== 'all' || statusFilter !== 'all'
                    ? 'Try adjusting your search or filters.'
                    : 'Get started by adding your first user.'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredUsers.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <Avatar className="h-12 w-12">
                        <AvatarImage src="" alt={user.name} />
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          {getInitials(user.name)}
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {user.name}
                          </h3>
                          {user.is_representative && (
                            <Badge variant="outline" className="text-xs">
                              Representative
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 truncate">{user.email}</p>
                        {user.company && (
                          <p className="text-xs text-gray-400 truncate">{user.company}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      {/* Role Badge */}
                      <Badge className={getRoleColor(user.role)}>
                        {snakeToTitle(user.role)}
                      </Badge>

                      {/* Status Badge */}
                      <Badge className={getStatusColor(user.status)}>
                        {snakeToTitle(user.status)}
                      </Badge>

                      {/* Last Login */}
                      <div className="text-xs text-gray-500 text-right min-w-0">
                        <p>Joined {formatDate(user.created_at, { month: 'short', day: 'numeric' })}</p>
                        {user.last_login_at && (
                          <p>Last login {formatDate(user.last_login_at, { month: 'short', day: 'numeric' })}</p>
                        )}
                      </div>

                      {/* Actions Menu */}
                      {currentUser.role === UserRole.SUPER_ADMIN && user.id !== currentUser.id && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            
                            {/* Role Management */}
                            <DropdownMenuLabel className="text-xs">Change Role</DropdownMenuLabel>
                            {Object.values(UserRole).map((role) => (
                              <DropdownMenuItem
                                key={role}
                                onClick={() => handleRoleChange(user.id, role)}
                                disabled={user.role === role}
                              >
                                <Shield className="mr-2 h-4 w-4" />
                                {snakeToTitle(role)}
                              </DropdownMenuItem>
                            ))}
                            
                            <DropdownMenuSeparator />
                            
                            {/* Status Management */}
                            <DropdownMenuLabel className="text-xs">Change Status</DropdownMenuLabel>
                            {Object.values(UserStatus).map((status) => (
                              <DropdownMenuItem
                                key={status}
                                onClick={() => handleStatusChange(user.id, status)}
                                disabled={user.status === status}
                              >
                                {snakeToTitle(status)}
                              </DropdownMenuItem>
                            ))}
                            
                            <DropdownMenuSeparator />
                            
                            <DropdownMenuItem>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit User
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDeleteUser(user.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete User
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
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
    </AdminGuard>
  );
}