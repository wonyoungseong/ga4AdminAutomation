"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  FileText, 
  Shield, 
  Clock, 
  CheckCircle, 
  XCircle,
  MoreHorizontal,
  RefreshCw,
  Eye,
  Users,
  Building,
  BarChart3,
  AlertTriangle
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { typeSafeApiClient } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { RoleGuard } from '@/components/rbac/role-guard';
import { PermissionRequestForm } from './permission-request-form';
import { PermissionStatusTracker, PermissionRequest, PermissionRequestStatus } from './permission-status-tracker';
import { PermissionApprovalInterface } from './permission-approval-interface';

interface PermissionStats {
  total_requests: number;
  pending_requests: number;
  approved_requests: number;
  rejected_requests: number;
  auto_approved_requests: number;
}

/**
 * Permission Management Page Component
 * 
 * 권한 관리 통합 페이지 컴포넌트
 * - 권한 요청 생성
 * - 권한 요청 상태 추적
 * - 관리자 승인/거부 인터페이스
 * - 통계 및 대시보드
 */
export function PermissionManagementPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [stats, setStats] = useState<PermissionStats>({
    total_requests: 0,
    pending_requests: 0,
    approved_requests: 0,
    rejected_requests: 0,
    auto_approved_requests: 0,
  });
  const [pendingRequests, setPendingRequests] = useState<PermissionRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<PermissionRequest | null>(null);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadStats(),
        loadPendingRequests(),
      ]);
    } catch (error) {
      console.error('Failed to load permission data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadStats = async () => {
    try {
      // For now, we'll calculate stats from the requests
      // In a real implementation, this would be a dedicated stats endpoint
      const myRequests = await typeSafeApiClient.request<PermissionRequest[]>(
        '/api/permission-requests/my-requests?limit=100'
      );
      
      const requests = Array.isArray(myRequests) ? myRequests : [];
      
      setStats({
        total_requests: requests.length,
        pending_requests: requests.filter(r => r.status === PermissionRequestStatus.PENDING).length,
        approved_requests: requests.filter(r => r.status === PermissionRequestStatus.APPROVED).length,
        rejected_requests: requests.filter(r => r.status === PermissionRequestStatus.REJECTED).length,
        auto_approved_requests: requests.filter(r => r.auto_approved).length,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadPendingRequests = async () => {
    try {
      // Only load pending requests if user is admin
      if (user?.role && ['Admin', 'Super Admin'].includes(user.role)) {
        const requests = await typeSafeApiClient.request<PermissionRequest[]>(
          '/api/permission-requests/pending-approvals?limit=50'
        );
        setPendingRequests(Array.isArray(requests) ? requests : []);
      }
    } catch (error) {
      console.error('Failed to load pending requests:', error);
      setPendingRequests([]);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
  };

  const handleRequestCreated = (requestId: number) => {
    toast({
      title: '권한 요청 완료',
      description: '권한 요청이 성공적으로 제출되었습니다.',
    });
    loadData(); // Refresh data
  };

  const handleRequestUpdated = () => {
    loadData(); // Refresh data
  };

  const handleViewRequest = (request: PermissionRequest) => {
    setSelectedRequest(request);
    setApprovalDialogOpen(true);
  };

  const handleApprovalComplete = () => {
    setSelectedRequest(null);
    loadData(); // Refresh data
  };

  const getStatusBadge = (status: PermissionRequestStatus, autoApproved: boolean = false) => {
    switch (status) {
      case PermissionRequestStatus.PENDING:
        return (
          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
            <Clock className="h-3 w-3 mr-1" />
            승인 대기
          </Badge>
        );
      case PermissionRequestStatus.APPROVED:
        return (
          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            {autoApproved ? '자동 승인' : '승인됨'}
          </Badge>
        );
      case PermissionRequestStatus.REJECTED:
        return (
          <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
            <XCircle className="h-3 w-3 mr-1" />
            거부됨
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPermissionLevelBadge = (level: string) => {
    const levelMap: Record<string, { label: string; color: string }> = {
      'VIEWER': { label: '뷰어', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
      'ANALYST': { label: '분석가', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' },
      'MARKETER': { label: '마케터', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
      'EDITOR': { label: '편집자', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
      'ADMINISTRATOR': { label: '관리자', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
    };

    const levelInfo = levelMap[level] || { label: level, color: 'bg-gray-100 text-gray-800' };
    
    return (
      <Badge className={levelInfo.color}>
        <Shield className="h-3 w-3 mr-1" />
        {levelInfo.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-64"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold korean-text">권한 관리</h1>
          <p className="text-gray-600 korean-text">
            GA4 속성 접근 권한 요청 및 관리
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
          <PermissionRequestForm
            onSuccess={handleRequestCreated}
            trigger={
              <Button>
                <FileText className="h-4 w-4 mr-2" />
                권한 요청
              </Button>
            }
          />
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 korean-text">전체 요청</p>
                <p className="text-2xl font-bold">{stats.total_requests}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 korean-text">승인 대기</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending_requests}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 korean-text">승인됨</p>
                <p className="text-2xl font-bold text-green-600">{stats.approved_requests}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 korean-text">자동 승인</p>
                <p className="text-2xl font-bold text-blue-600">{stats.auto_approved_requests}</p>
              </div>
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="my-requests" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="my-requests" className="korean-text">내 요청</TabsTrigger>
          <RoleGuard allowedRoles={['Admin', 'Super Admin']}>
            <TabsTrigger value="pending-approvals" className="korean-text">
              승인 대기 ({pendingRequests.length})
            </TabsTrigger>
          </RoleGuard>
          <TabsTrigger value="all-requests" className="korean-text">전체 현황</TabsTrigger>
        </TabsList>

        {/* My Requests Tab */}
        <TabsContent value="my-requests">
          <PermissionStatusTracker
            userId={user?.id}
            onRequestUpdated={handleRequestUpdated}
          />
        </TabsContent>

        {/* Pending Approvals Tab (Admin only) */}
        <RoleGuard allowedRoles={['Admin', 'Super Admin']}>
          <TabsContent value="pending-approvals">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 korean-text">
                  <AlertTriangle className="h-5 w-5" />
                  승인 대기 중인 요청
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pendingRequests.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="korean-text">승인 대기 중인 요청이 없습니다.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="korean-text">요청자</TableHead>
                          <TableHead className="korean-text">클라이언트</TableHead>
                          <TableHead className="korean-text">권한 레벨</TableHead>
                          <TableHead className="korean-text">요청일</TableHead>
                          <TableHead className="korean-text">필요 승인</TableHead>
                          <TableHead className="w-12"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pendingRequests.map((request) => (
                          <TableRow key={request.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{request.target_email}</div>
                                {request.user_name && (
                                  <div className="text-sm text-gray-500">
                                    {request.user_name}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Building className="h-4 w-4 text-gray-400" />
                                {request.client_name || `클라이언트 ${request.client_id}`}
                              </div>
                            </TableCell>
                            <TableCell>
                              {getPermissionLevelBadge(request.permission_level)}
                            </TableCell>
                            <TableCell>
                              {new Date(request.submitted_at).toLocaleDateString('ko-KR')}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">
                                {request.requires_approval_from_role || 'Admin'}
                              </Badge>
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
                                  <DropdownMenuItem onClick={() => handleViewRequest(request)}>
                                    <Eye className="h-4 w-4 mr-2" />
                                    검토 및 승인
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </RoleGuard>

        {/* All Requests Tab */}
        <TabsContent value="all-requests">
          <PermissionStatusTracker
            showActions={user?.role && ['Admin', 'Super Admin'].includes(user.role)}
            onRequestUpdated={handleRequestUpdated}
          />
        </TabsContent>
      </Tabs>

      {/* Approval Dialog */}
      {selectedRequest && (
        <PermissionApprovalInterface
          request={selectedRequest}
          open={approvalDialogOpen}
          onOpenChange={setApprovalDialogOpen}
          onApproved={handleApprovalComplete}
          onRejected={handleApprovalComplete}
        />
      )}
    </div>
  );
}