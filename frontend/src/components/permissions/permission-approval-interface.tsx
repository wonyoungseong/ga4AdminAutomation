"use client";

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  User, 
  Building, 
  Shield,
  Calendar,
  FileText,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { typeSafeApiClient } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/utils';
import { PermissionRequest, PermissionRequestStatus } from './permission-status-tracker';

// Approval form schemas
const approvalSchema = z.object({
  processing_notes: z.string().optional(),
  expires_in_days: z.number()
    .min(1, '최소 1일 이상이어야 합니다.')
    .max(365, '최대 365일까지 가능합니다.')
    .default(30),
});

const rejectionSchema = z.object({
  processing_notes: z.string()
    .min(10, '거부 사유를 최소 10자 이상 입력해주세요.')
    .max(500, '거부 사유는 500자를 초과할 수 없습니다.'),
});

type ApprovalFormData = z.infer<typeof approvalSchema>;
type RejectionFormData = z.infer<typeof rejectionSchema>;

interface PermissionApprovalInterfaceProps {
  request: PermissionRequest;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApproved?: (requestId: number) => void;
  onRejected?: (requestId: number) => void;
}

/**
 * Permission Approval Interface Component
 * 
 * 권한 요청 승인/거부 인터페이스 컴포넌트
 * Admin/Super Admin 사용자가 권한 요청을 검토하고 승인/거부할 수 있음
 */
export function PermissionApprovalInterface({
  request,
  open,
  onOpenChange,
  onApproved,
  onRejected
}: PermissionApprovalInterfaceProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const approvalForm = useForm<ApprovalFormData>({
    resolver: zodResolver(approvalSchema),
    defaultValues: {
      expires_in_days: 30,
    },
  });

  const rejectionForm = useForm<RejectionFormData>({
    resolver: zodResolver(rejectionSchema),
    defaultValues: {
      processing_notes: '',
    },
  });

  // Reset forms when dialog opens/closes
  useEffect(() => {
    if (open) {
      setAction(null);
      approvalForm.reset();
      rejectionForm.reset();
    }
  }, [open]);

  const handleApprove = async (data: ApprovalFormData) => {
    try {
      setSubmitting(true);
      
      await typeSafeApiClient.request(`/api/permission-requests/${request.id}/approve`, {
        method: 'PUT',
        body: JSON.stringify({
          processing_notes: data.processing_notes || '승인됨',
        }),
      });

      toast({
        title: '권한 요청 승인 완료',
        description: `${request.target_email}의 권한 요청이 승인되었습니다.`,
      });

      onOpenChange(false);
      onApproved?.(request.id);
    } catch (error: any) {
      toast({
        title: '승인 실패',
        description: error.message || '권한 요청 승인 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async (data: RejectionFormData) => {
    try {
      setSubmitting(true);
      
      await typeSafeApiClient.request(`/api/permission-requests/${request.id}/reject`, {
        method: 'PUT',
        body: JSON.stringify({
          processing_notes: data.processing_notes,
        }),
      });

      toast({
        title: '권한 요청 거부 완료',
        description: `${request.target_email}의 권한 요청이 거부되었습니다.`,
      });

      onOpenChange(false);
      onRejected?.(request.id);
    } catch (error: any) {
      toast({
        title: '거부 실패',
        description: error.message || '권한 요청 거부 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getPermissionLevelInfo = (level: string) => {
    const levelMap: Record<string, { label: string; description: string; color: string }> = {
      'VIEWER': { 
        label: '뷰어', 
        description: '데이터 조회만 가능',
        color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      },
      'ANALYST': { 
        label: '분석가', 
        description: '표준 보고서 및 분석',
        color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      },
      'MARKETER': { 
        label: '마케터', 
        description: '마케팅 활동 및 캠페인 관리',
        color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      },
      'EDITOR': { 
        label: '편집자', 
        description: '속성 설정 및 구성 변경',
        color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      },
      'ADMINISTRATOR': { 
        label: '관리자', 
        description: '전체 관리 권한',
        color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      },
    };

    return levelMap[level] || { 
      label: level, 
      description: '알 수 없는 권한',
      color: 'bg-gray-100 text-gray-800' 
    };
  };

  const canApprove = () => {
    if (!user) return false;
    
    // Super Admin can approve all requests
    if (user.role === 'Super Admin') return true;
    
    // Admin can approve requests that require Admin approval
    if (user.role === 'Admin' && request.requires_approval_from_role === 'admin') {
      return true;
    }
    
    return false;
  };

  if (!canApprove()) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="korean-text">권한 부족</DialogTitle>
            <DialogDescription className="korean-text">
              이 권한 요청을 승인할 권한이 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => onOpenChange(false)}>
              확인
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 korean-text">
            <Shield className="h-5 w-5" />
            권한 요청 검토
          </DialogTitle>
          <DialogDescription className="korean-text">
            다음 권한 요청을 검토하고 승인 또는 거부하세요.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Request Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg korean-text">요청 정보</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* User Info */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">대상 사용자:</span>
                </div>
                <span className="font-mono">{request.target_email}</span>
              </div>

              {/* Client Info */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Building className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">클라이언트:</span>
                </div>
                <span>{request.client_name || `클라이언트 ${request.client_id}`}</span>
              </div>

              {/* GA4 Property */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">GA4 속성:</span>
                </div>
                <div>
                  <div className="font-mono text-sm">{request.ga_property_id}</div>
                  {request.property_name && (
                    <div className="text-sm text-gray-500">{request.property_name}</div>
                  )}
                </div>
              </div>

              {/* Permission Level */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">권한 레벨:</span>
                </div>
                <div className="flex items-center gap-2">
                  {(() => {
                    const levelInfo = getPermissionLevelInfo(request.permission_level);
                    return (
                      <>
                        <Badge className={levelInfo.color}>
                          {levelInfo.label}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          {levelInfo.description}
                        </span>
                      </>
                    );
                  })()}
                </div>
              </div>

              {/* Duration */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">요청 기간:</span>
                </div>
                <span>{request.requested_duration_days}일</span>
              </div>

              {/* Submitted Date */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">요청일:</span>
                </div>
                <span>{formatDate(request.submitted_at)}</span>
              </div>

              {/* Business Justification */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">업무 사유:</span>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm whitespace-pre-wrap korean-text">
                    {request.business_justification}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Approval/Rejection Actions */}
          {!action && (
            <div className="flex justify-center gap-4">
              <Button
                onClick={() => setAction('approve')}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                승인
              </Button>
              <Button
                onClick={() => setAction('reject')}
                variant="destructive"
              >
                <XCircle className="h-4 w-4 mr-2" />
                거부
              </Button>
            </div>
          )}

          {/* Approval Form */}
          {action === 'approve' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-green-700 korean-text">권한 요청 승인</CardTitle>
              </CardHeader>
              <CardContent>
                <Form {...approvalForm}>
                  <form onSubmit={approvalForm.handleSubmit(handleApprove)} className="space-y-4">
                    <FormField
                      control={approvalForm.control}
                      name="processing_notes"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="korean-text">승인 메모 (선택사항)</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="승인 관련 추가 메모가 있으면 입력하세요..."
                              className="korean-text"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription className="korean-text">
                        승인 시 요청한 기간({request.requested_duration_days}일) 동안 권한이 부여됩니다.
                        GA4에서 실제 권한 부여는 비동기적으로 처리됩니다.
                      </AlertDescription>
                    </Alert>

                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setAction(null)}
                        disabled={submitting}
                      >
                        취소
                      </Button>
                      <Button
                        type="submit"
                        className="bg-green-600 hover:bg-green-700"
                        disabled={submitting}
                      >
                        {submitting ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            승인 중...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            승인 확정
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </Form>
              </CardContent>
            </Card>
          )}

          {/* Rejection Form */}
          {action === 'reject' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-red-700 korean-text">권한 요청 거부</CardTitle>
              </CardHeader>
              <CardContent>
                <Form {...rejectionForm}>
                  <form onSubmit={rejectionForm.handleSubmit(handleReject)} className="space-y-4">
                    <FormField
                      control={rejectionForm.control}
                      name="processing_notes"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="korean-text">거부 사유 *</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="권한 요청을 거부하는 구체적인 사유를 입력하세요..."
                              className="min-h-[100px] korean-text"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription className="korean-text">
                        거부 시 요청자에게 거부 사유가 전달됩니다.
                        명확하고 건설적인 피드백을 제공해주세요.
                      </AlertDescription>
                    </Alert>

                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setAction(null)}
                        disabled={submitting}
                      >
                        취소
                      </Button>
                      <Button
                        type="submit"
                        variant="destructive"
                        disabled={submitting}
                      >
                        {submitting ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            거부 중...
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 mr-2" />
                            거부 확정
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </Form>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}