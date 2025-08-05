"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { User, UserCreate, UserUpdate } from '@/types/api';
import { UsersDataTable } from './users-data-table';
import { UserForm } from './user-form';
import { BulkActionsDialog } from './bulk-actions-dialog';
import { typeSafeApiClient } from '@/lib/api-client';
import { useAuth } from '@/contexts/auth-context';
import { RoleGuard } from '@/components/rbac/role-guard';
import { cn } from '@/lib/utils';
import { 
  Users, 
  UserPlus, 
  Download, 
  Upload,
  RefreshCw,
  Filter,
  Settings
} from 'lucide-react';

/**
 * User Management Page Component
 * 
 * Complete user management interface with RBAC controls,
 * Korean localization, and comprehensive user operations
 */
export function UserManagementPage({ className }: { className?: string }) {
  const { user: currentUser } = useAuth();
  const { toast } = useToast();
  
  // State management
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);
  
  // Dialog states
  const [userFormOpen, setUserFormOpen] = useState(false);
  const [bulkActionOpen, setBulkActionOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>();
  const [bulkAction, setBulkAction] = useState<'approve' | 'suspend' | 'delete' | 'change_role' | 'change_status' | null>(null);

  // Load users
  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await typeSafeApiClient.getUsers(1, 100);
      setUsers(response.items);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast({
        title: '사용자 로드 실패',
        description: '사용자 목록을 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Initial load
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Handle user creation
  const handleCreateUser = useCallback(async (userData: UserCreate) => {
    try {
      await typeSafeApiClient.createUser(userData);
      toast({
        title: '사용자 추가 완료',
        description: `${userData.name}님이 성공적으로 추가되었습니다.`,
      });
      await loadUsers();
    } catch (error) {
      console.error('Failed to create user:', error);
      toast({
        title: '사용자 추가 실패',
        description: '사용자 추가 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
      throw error;
    }
  }, [toast, loadUsers]);

  // Handle user update
  const handleUpdateUser = useCallback(async (userData: UserUpdate) => {
    if (!editingUser) return;
    
    try {
      await typeSafeApiClient.updateUser(editingUser.id, userData);
      toast({
        title: '사용자 수정 완료',
        description: `${userData.name}님의 정보가 성공적으로 수정되었습니다.`,
      });
      await loadUsers();
      setEditingUser(undefined);
    } catch (error) {
      console.error('Failed to update user:', error);
      toast({
        title: '사용자 수정 실패',
        description: '사용자 정보 수정 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
      throw error;
    }
  }, [editingUser, toast, loadUsers]);

  // Handle user edit
  const handleUserEdit = useCallback((user: User) => {
    setEditingUser(user);
    setUserFormOpen(true);
  }, []);

  // Handle user delete
  const handleUserDelete = useCallback(async (userId: number) => {
    try {
      await typeSafeApiClient.deleteUser(userId);
      toast({
        title: '사용자 삭제 완료',
        description: '사용자가 성공적으로 삭제되었습니다.',
      });
      await loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast({
        title: '사용자 삭제 실패',
        description: '사용자 삭제 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  }, [toast, loadUsers]);

  // Handle user approval
  const handleUserApprove = useCallback(async (userId: number) => {
    try {
      await typeSafeApiClient.approveUser(userId, { approved: true });
      toast({
        title: '사용자 승인 완료',
        description: '사용자가 성공적으로 승인되었습니다.',
      });
      await loadUsers();
    } catch (error) {
      console.error('Failed to approve user:', error);
      toast({
        title: '사용자 승인 실패',
        description: '사용자 승인 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  }, [toast, loadUsers]);

  // Handle user suspend
  const handleUserSuspend = useCallback(async (userId: number) => {
    try {
      const user = users.find(u => u.id === userId);
      if (!user) return;

      const newStatus = user.status === 'suspended' ? 'active' : 'suspended';
      await typeSafeApiClient.updateUser(userId, { status: newStatus });
      
      toast({
        title: newStatus === 'suspended' ? '사용자 정지 완료' : '사용자 정지 해제 완료',
        description: `사용자가 성공적으로 ${newStatus === 'suspended' ? '정지' : '정지 해제'}되었습니다.`,
      });
      await loadUsers();
    } catch (error) {
      console.error('Failed to suspend/unsuspend user:', error);
      toast({
        title: '사용자 상태 변경 실패',
        description: '사용자 상태 변경 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  }, [users, toast, loadUsers]);

  // Handle bulk actions
  const handleBulkAction = useCallback((action: string, userIds: number[]) => {
    const selectedUsersData = users.filter(user => userIds.includes(user.id));
    setSelectedUsers(selectedUsersData);
    setBulkAction(action as any);
    setBulkActionOpen(true);
  }, [users]);

  // Handle bulk action confirmation
  const handleBulkActionConfirm = useCallback(async (action: string, data?: any) => {
    try {
      const userIds = selectedUsers.map(u => u.id);
      
      switch (action) {
        case 'approve':
          for (const userId of userIds) {
            await typeSafeApiClient.approveUser(userId, { approved: true, ...data });
          }
          break;
        case 'suspend':
          for (const userId of userIds) {
            await typeSafeApiClient.updateUser(userId, { status: 'suspended' });
          }
          break;
        case 'delete':
          for (const userId of userIds) {
            await typeSafeApiClient.deleteUser(userId);
          }
          break;
        case 'change_role':
          for (const userId of userIds) {
            await typeSafeApiClient.updateUser(userId, { role: data.role });
          }
          break;
        case 'change_status':
          for (const userId of userIds) {
            await typeSafeApiClient.updateUser(userId, { status: data.status });
          }
          break;
      }

      toast({
        title: '대량 작업 완료',
        description: `${selectedUsers.length}명의 사용자에 대한 작업이 완료되었습니다.`,
      });
      
      await loadUsers();
      setSelectedUsers([]);
      setBulkAction(null);
    } catch (error) {
      console.error('Bulk action failed:', error);
      toast({
        title: '대량 작업 실패',
        description: '대량 작업 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
      throw error;
    }
  }, [selectedUsers, toast, loadUsers]);

  // Statistics
  const stats = React.useMemo(() => {
    return {
      total: users.length,
      active: users.filter(u => u.status === 'active').length,
      pending: users.filter(u => u.registration_status === 'pending_verification').length,
      suspended: users.filter(u => u.status === 'suspended').length,
      admins: users.filter(u => u.role === 'Admin' || u.role === 'Super Admin').length,
    };
  }, [users]);

  return (
    <div className={cn('space-y-6', className)}>
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold korean-text">사용자 관리</h1>
          <p className="text-gray-600 dark:text-gray-400 korean-text">
            시스템 사용자의 계정과 권한을 관리합니다.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={loadUsers}>
            <RefreshCw className="h-4 w-4 mr-1" />
            새로고침
          </Button>
          <RoleGuard allowedRoles={['Super Admin', 'Admin']}>
            <Button onClick={() => setUserFormOpen(true)}>
              <UserPlus className="h-4 w-4 mr-1" />
              사용자 추가
            </Button>
          </RoleGuard>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-sm font-medium korean-text">전체 사용자</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <div>
                <p className="text-sm font-medium korean-text">활성</p>
                <p className="text-2xl font-bold text-green-600">{stats.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div>
                <p className="text-sm font-medium korean-text">승인 대기</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div>
                <p className="text-sm font-medium korean-text">정지됨</p>
                <p className="text-2xl font-bold text-red-600">{stats.suspended}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <div>
                <p className="text-sm font-medium korean-text">관리자</p>
                <p className="text-2xl font-bold text-purple-600">{stats.admins}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Users Data Table */}
      <UsersDataTable
        users={users}
        loading={loading}
        onUserEdit={handleUserEdit}
        onUserDelete={handleUserDelete}
        onUserApprove={handleUserApprove}
        onUserSuspend={handleUserSuspend}
        onBulkAction={handleBulkAction}
        onRefresh={loadUsers}
      />

      {/* User Form Dialog */}
      <UserForm
        user={editingUser}
        open={userFormOpen}
        onOpenChange={(open) => {
          setUserFormOpen(open);
          if (!open) setEditingUser(undefined);
        }}
        onSubmit={editingUser ? handleUpdateUser : handleCreateUser}
        mode={editingUser ? 'edit' : 'create'}
      />

      {/* Bulk Actions Dialog */}
      <BulkActionsDialog
        open={bulkActionOpen}
        onOpenChange={setBulkActionOpen}
        selectedUsers={selectedUsers}
        action={bulkAction}
        onConfirm={handleBulkActionConfirm}
      />
    </div>
  );
}