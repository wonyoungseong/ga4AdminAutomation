"use client";

import React, { useState, useMemo, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { User, UserRole, UserStatus, RegistrationStatus } from '@/types/api';
import { RoleBadge } from '@/components/rbac/role-badge';
import { RoleGuard } from '@/components/rbac/role-guard';
import { useAuth } from '@/contexts/auth-context';
import { cn } from '@/lib/utils';
import { 
  Search, 
  Filter, 
  MoreHorizontal, 
  UserPlus, 
  Download,
  RefreshCw,
  Users,
  Shield,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

interface UsersDataTableProps {
  users: User[];
  loading?: boolean;
  onUserEdit?: (user: User) => void;
  onUserDelete?: (userId: number) => void;
  onUserApprove?: (userId: number) => void;
  onUserSuspend?: (userId: number) => void;
  onBulkAction?: (action: string, userIds: number[]) => void;
  onRefresh?: () => void;
  className?: string;
}

/**
 * Users Data Table Component
 * 
 * Advanced user management table with RBAC filtering,
 * Korean localization, and bulk operations support
 */
export function UsersDataTable({
  users,
  loading = false,
  onUserEdit,
  onUserDelete,
  onUserApprove,
  onUserSuspend,
  onBulkAction,
  onRefresh,
  className
}: UsersDataTableProps) {
  const { user: currentUser } = useAuth();
  const [selectedUsers, setSelectedUsers] = useState<Set<number>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<UserStatus | 'all'>('all');
  const [registrationFilter, setRegistrationFilter] = useState<RegistrationStatus | 'all'>('all');
  const [sortField, setSortField] = useState<keyof User>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Filter and sort users
  const filteredAndSortedUsers = useMemo(() => {
    let filtered = users.filter(user => {
      const searchMatch = searchTerm === '' || 
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.company?.toLowerCase().includes(searchTerm.toLowerCase());

      const roleMatch = roleFilter === 'all' || user.role === roleFilter;
      const statusMatch = statusFilter === 'all' || user.status === statusFilter;
      const registrationMatch = registrationFilter === 'all' || user.registration_status === registrationFilter;

      return searchMatch && roleMatch && statusMatch && registrationMatch;
    });

    // Sort users
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (aValue === bValue) return 0;
      
      const comparison = aValue < bValue ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [users, searchTerm, roleFilter, statusFilter, registrationFilter, sortField, sortDirection]);

  // Handle row selection
  const handleRowSelect = useCallback((userId: number, selected: boolean) => {
    setSelectedUsers(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(userId);
      } else {
        newSet.delete(userId);
      }
      return newSet;
    });
  }, []);

  // Handle select all
  const handleSelectAll = useCallback((selected: boolean) => {
    if (selected) {
      setSelectedUsers(new Set(filteredAndSortedUsers.map(u => u.id)));
    } else {
      setSelectedUsers(new Set());
    }
  }, [filteredAndSortedUsers]);

  // Handle bulk actions
  const handleBulkAction = useCallback((action: string) => {
    if (selectedUsers.size === 0) return;
    onBulkAction?.(action, Array.from(selectedUsers));
    setSelectedUsers(new Set());
  }, [selectedUsers, onBulkAction]);

  // Handle sort
  const handleSort = useCallback((field: keyof User) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField]);

  // Status display helpers
  const getStatusDisplay = (user: User) => {
    const statusStyles: Record<UserStatus, string> = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
      suspended: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    };

    const statusLabels: Record<UserStatus, string> = {
      active: '활성',
      inactive: '비활성',
      suspended: '정지됨'
    };

    return (
      <Badge className={statusStyles[user.status]}>
        {statusLabels[user.status]}
      </Badge>
    );
  };

  const getRegistrationStatusDisplay = (status: RegistrationStatus) => {
    const statusStyles: Record<RegistrationStatus, string> = {
      pending_verification: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      verified: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    };

    const statusLabels: Record<RegistrationStatus, string> = {
      pending_verification: '이메일 인증 대기',
      verified: '인증 완료',
      approved: '승인됨',
      rejected: '거부됨'
    };

    return (
      <Badge className={statusStyles[status]}>
        {statusLabels[status]}
      </Badge>
    );
  };

  // Statistics
  const stats = useMemo(() => {
    return {
      total: users.length,
      active: users.filter(u => u.status === 'active').length,
      pending: users.filter(u => u.registration_status === 'pending_verification').length,
      suspended: users.filter(u => u.status === 'suspended').length
    };
  }, [users]);

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex space-x-4">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              <span className="korean-text">사용자 관리</span>
            </CardTitle>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                <span>전체 {stats.total}명</span>
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>활성 {stats.active}명</span>
              </div>
              <div className="flex items-center gap-1">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span>대기 {stats.pending}명</span>
              </div>
              <div className="flex items-center gap-1">
                <Shield className="h-4 w-4 text-red-600" />
                <span>정지 {stats.suspended}명</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <RefreshCw className="h-4 w-4 mr-1" />
              새로고침
            </Button>
            <RoleGuard allowedRoles={['Super Admin', 'Admin']}>
              <Button size="sm">
                <UserPlus className="h-4 w-4 mr-1" />
                사용자 추가
              </Button>
            </RoleGuard>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="이름, 이메일, 회사명으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 korean-text"
            />
          </div>
          <Select value={roleFilter} onValueChange={(value) => setRoleFilter(value as UserRole | 'all')}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="역할 필터" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">모든 역할</SelectItem>
              <SelectItem value="Super Admin">최고 관리자</SelectItem>
              <SelectItem value="Admin">관리자</SelectItem>
              <SelectItem value="Requester">요청자</SelectItem>
              <SelectItem value="Viewer">뷰어</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as UserStatus | 'all')}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="상태 필터" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">모든 상태</SelectItem>
              <SelectItem value="active">활성</SelectItem>
              <SelectItem value="inactive">비활성</SelectItem>
              <SelectItem value="suspended">정지됨</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Bulk Actions */}
        {selectedUsers.size > 0 && (
          <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <span className="text-sm font-medium korean-text">
              {selectedUsers.size}명 선택됨
            </span>
            <div className="flex gap-2 ml-auto">
              <RoleGuard allowedRoles={['Super Admin', 'Admin']}>
                <Button size="sm" variant="outline" onClick={() => handleBulkAction('approve')}>
                  승인
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleBulkAction('suspend')}>
                  정지
                </Button>
                <Button size="sm" variant="destructive" onClick={() => handleBulkAction('delete')}>
                  삭제
                </Button>
              </RoleGuard>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedUsers.size === filteredAndSortedUsers.length && filteredAndSortedUsers.length > 0}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 korean-text"
                  onClick={() => handleSort('name')}
                >
                  이름 {sortField === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 korean-text"
                  onClick={() => handleSort('email')}
                >
                  이메일 {sortField === 'email' && (sortDirection === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead className="korean-text">역할</TableHead>
                <TableHead className="korean-text">상태</TableHead>
                <TableHead className="korean-text">등록 상태</TableHead>
                <TableHead className="korean-text">회사</TableHead>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 korean-text"
                  onClick={() => handleSort('created_at')}
                >
                  가입일 {sortField === 'created_at' && (sortDirection === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSortedUsers.map((user) => (
                <TableRow key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <TableCell>
                    <Checkbox
                      checked={selectedUsers.has(user.id)}
                      onCheckedChange={(checked) => handleRowSelect(user.id, checked as boolean)}
                    />
                  </TableCell>
                  <TableCell className="font-medium korean-text">
                    <div>
                      <div>{user.name}</div>
                      {user.is_representative && (
                        <Badge variant="outline" className="text-xs mt-1">
                          대표자
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{user.email}</TableCell>
                  <TableCell>
                    <RoleBadge role={user.role} status={user.status} size="sm" />
                  </TableCell>
                  <TableCell>{getStatusDisplay(user)}</TableCell>
                  <TableCell>{getRegistrationStatusDisplay(user.registration_status)}</TableCell>
                  <TableCell className="korean-text">{user.company || '-'}</TableCell>
                  <TableCell className="text-sm text-gray-500">
                    {new Date(user.created_at).toLocaleDateString('ko-KR')}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel className="korean-text">작업</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => onUserEdit?.(user)}>
                          편집
                        </DropdownMenuItem>
                        <RoleGuard allowedRoles={['Super Admin', 'Admin']}>
                          {user.registration_status === 'verified' && (
                            <DropdownMenuItem onClick={() => onUserApprove?.(user.id)}>
                              승인
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => onUserSuspend?.(user.id)}>
                            {user.status === 'suspended' ? '정지 해제' : '정지'}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            className="text-red-600"
                            onClick={() => onUserDelete?.(user.id)}
                          >
                            삭제
                          </DropdownMenuItem>
                        </RoleGuard>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {filteredAndSortedUsers.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="korean-text">조건에 맞는 사용자가 없습니다.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}