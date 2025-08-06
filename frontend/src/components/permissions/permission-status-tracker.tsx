"use client";

import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  MoreHorizontal,
  RefreshCw,
  Eye,
  Trash2,
  Calendar,
  User,
  Building,
  Shield
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { typeSafeApiClient } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/utils';

// Permission request status enum (matches backend)
export enum PermissionRequestStatus {
  PENDING = 'pending',
  APPROVED = 'approved', 
  REJECTED = 'rejected',
  CANCELLED = 'cancelled',
  EXPIRED = 'expired'
}

// Permission request interface
export interface PermissionRequest {
  id: number;
  user_id: number;
  client_id: number;
  ga_property_id: string;
  target_email: string;
  permission_level: string;
  business_justification: string;
  requested_duration_days: number;
  status: PermissionRequestStatus;
  auto_approved: boolean;
  requires_approval_from_role: string | null;
  submitted_at: string;
  processed_at: string | null;
  processed_by_id: number | null;
  processing_notes: string | null;
  expires_at: string | null;
  // Related data
  user_name?: string;
  user_email?: string;
  client_name?: string;
  property_name?: string;
  processed_by_name?: string;
}

interface PermissionStatusTrackerProps {
  userId?: number; // If provided, show only requests for this user
  showActions?: boolean;
  onRequestUpdated?: (requestId: number) => void;
  className?: string;
}

/**
 * Permission Status Tracker Component
 * 
 * 권한 요청 상태 추적 컴포넌트
 * 실시간 상태 업데이트 및 액션 지원
 */
export function PermissionStatusTracker({
  userId,
  showActions = true,
  onRequestUpdated,
  className
}: PermissionStatusTrackerProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [requests, setRequests] = useState<PermissionRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadRequests();
  }, [userId]);

  const loadRequests = async () => {
    try {
      setLoading(true);
      
      // Use appropriate endpoint based on props
      let endpoint = '/api/permission-requests/my-requests';
      const params = new URLSearchParams({
        limit: '50',
        offset: '0',
      });

      if (userId && user?.role && ['Admin', 'Super Admin'].includes(user.role)) {
        // Admins can view all requests or filter by user
        endpoint = '/api/permission-requests/pending-approvals';
      }

      const response = await typeSafeApiClient.request<PermissionRequest[]>(`${endpoint}?${params}`);
      setRequests(Array.isArray(response) ? response : []);
    } catch (error: any) {
      toast({
        title: '데이터 로드 실패',
        description: error.message || '권한 요청 목록을 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadRequests();
  };

  const handleCancelRequest = async (requestId: number) => {
    try {
      await typeSafeApiClient.request(`/api/permission-requests/${requestId}`, {
        method: 'DELETE',
      });
      
      toast({
        title: '요청 취소 완료',
        description: '권한 요청이 성공적으로 취소되었습니다.',
      });
      
      await loadRequests();
      onRequestUpdated?.(requestId);
    } catch (error: any) {
      toast({
        title: '요청 취소 실패',
        description: error.message || '권한 요청 취소 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    }
  };

  const getStatusDisplay = (status: PermissionRequestStatus, autoApproved: boolean) => {
    const baseClasses = "inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full";
    
    switch (status) {
      case PermissionRequestStatus.PENDING:
        return (
          <Badge className={`${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`}>
            <Clock className="h-3 w-3" />
            승인 대기
          </Badge>
        );
      case PermissionRequestStatus.APPROVED:
        return (
          <Badge className={`${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`}>
            <CheckCircle className="h-3 w-3" />
            {autoApproved ? '자동 승인' : '승인됨'}
          </Badge>
        );
      case PermissionRequestStatus.REJECTED:
        return (
          <Badge className={`${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`}>
            <XCircle className="h-3 w-3" />
            거부됨
          </Badge>
        );
      case PermissionRequestStatus.CANCELLED:
        return (
          <Badge className={`${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`}>
            <XCircle className="h-3 w-3" />
            취소됨
          </Badge>
        );
      case PermissionRequestStatus.EXPIRED:
        return (
          <Badge className={`${baseClasses} bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200`}>
            <AlertTriangle className="h-3 w-3" />
            만료됨
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {status}
          </Badge>
        );
    }
  };

  const getPermissionLevelDisplay = (level: string) => {
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
      <Card className={className}>
        <CardHeader>
          <CardTitle className="korean-text">권한 요청 현황</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
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
          <CardTitle className="flex items-center gap-2 korean-text">
            <Clock className="h-5 w-5" />
            권한 요청 현황
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        {requests.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="korean-text">권한 요청이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="korean-text">요청 정보</TableHead>
                  <TableHead className="korean-text">권한 레벨</TableHead>
                  <TableHead className="korean-text">상태</TableHead>
                  <TableHead className="korean-text">요청일</TableHead>
                  <TableHead className="korean-text">처리일</TableHead>
                  {showActions && <TableHead className="w-12"></TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((request) => (
                  <TableRow key={request.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="font-medium korean-text">
                            {request.target_email}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Building className="h-3 w-3" />
                          <span>{request.client_name || `클라이언트 ${request.client_id}`}</span>
                        </div>
                        <div className="text-xs text-gray-400 font-mono">
                          {request.ga_property_id}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getPermissionLevelDisplay(request.permission_level)}
                    </TableCell>
                    <TableCell>
                      {getStatusDisplay(request.status, request.auto_approved)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3 text-gray-400" />
                        {formatDate(request.submitted_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {request.processed_at ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-1 text-sm">
                            <Calendar className="h-3 w-3 text-gray-400" />
                            {formatDate(request.processed_at)}
                          </div>
                          {request.processed_by_name && (
                            <div className="text-xs text-gray-500">
                              처리자: {request.processed_by_name}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">-</span>
                      )}
                    </TableCell>
                    {showActions && (
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
                            <DropdownMenuItem>
                              <Eye className="h-4 w-4 mr-2" />
                              자세히 보기
                            </DropdownMenuItem>
                            {request.status === PermissionRequestStatus.PENDING && 
                             request.user_id === user?.id && (
                              <DropdownMenuItem 
                                className="text-red-600"
                                onClick={() => handleCancelRequest(request.id)}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                요청 취소
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}