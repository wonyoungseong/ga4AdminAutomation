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
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, FileText, Shield, Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { typeSafeApiClient } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { Client, GA4Property, UserRole } from '@/types/api';

// Permission levels based on backend enum
const PERMISSION_LEVELS = [
  { value: 'VIEWER', label: '뷰어', description: '데이터 조회만 가능' },
  { value: 'ANALYST', label: '분석가', description: '표준 보고서 및 분석' },
  { value: 'MARKETER', label: '마케터', description: '마케팅 활동 및 캠페인 관리' },
  { value: 'EDITOR', label: '편집자', description: '속성 설정 및 구성 변경' },
  { value: 'ADMINISTRATOR', label: '관리자', description: '전체 관리 권한' }
] as const;

type PermissionLevel = typeof PERMISSION_LEVELS[number]['value'];

// Form validation schema
const permissionRequestSchema = z.object({
  client_id: z.number({
    required_error: '클라이언트를 선택해주세요.',
  }),
  ga_property_id: z.string({
    required_error: 'GA4 속성을 선택해주세요.',
  }),
  target_email: z.string()
    .email('올바른 이메일 주소를 입력해주세요.')
    .min(1, '이메일을 입력해주세요.'),
  permission_level: z.enum(['VIEWER', 'ANALYST', 'MARKETER', 'EDITOR', 'ADMINISTRATOR'], {
    required_error: '권한 레벨을 선택해주세요.',
  }),
  business_justification: z.string()
    .min(10, '업무 사유를 최소 10자 이상 입력해주세요.')
    .max(500, '업무 사유는 500자를 초과할 수 없습니다.'),
  requested_duration_days: z.number()
    .min(1, '최소 1일 이상이어야 합니다.')
    .max(365, '최대 365일까지 가능합니다.')
    .default(30),
});

type PermissionRequestFormData = z.infer<typeof permissionRequestSchema>;

// Auto-approval rule type
interface AutoApprovalRule {
  permission_level: PermissionLevel;
  user_role: UserRole;
  auto_approved: boolean;
  requires_approval_from_role: UserRole | null;
  description: string;
}

interface PermissionRequestFormProps {
  trigger?: React.ReactNode;
  onSuccess?: (requestId: number) => void;
  onCancel?: () => void;
  defaultValues?: Partial<PermissionRequestFormData>;
  className?: string;
}

/**
 * Permission Request Form Component
 * 
 * 권한 요청 폼 컴포넌트 - React Hook Form + Zod 검증
 * Auto-approval 규칙 표시 및 GA4 속성 선택 지원
 */
export function PermissionRequestForm({
  trigger,
  onSuccess,
  onCancel,
  defaultValues,
  className
}: PermissionRequestFormProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  const [properties, setProperties] = useState<GA4Property[]>([]);
  const [autoApprovalRules, setAutoApprovalRules] = useState<AutoApprovalRule[]>([]);
  const [loadingClients, setLoadingClients] = useState(false);
  const [loadingProperties, setLoadingProperties] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<PermissionRequestFormData>({
    resolver: zodResolver(permissionRequestSchema),
    defaultValues: {
      requested_duration_days: 30,
      ...defaultValues,
    },
  });

  const selectedClientId = form.watch('client_id');
  const selectedPermissionLevel = form.watch('permission_level');

  // Load clients on form open
  useEffect(() => {
    if (open) {
      loadClients();
      loadAutoApprovalRules();
    }
  }, [open]);

  // Load properties when client is selected
  useEffect(() => {
    if (selectedClientId) {
      loadProperties(selectedClientId);
    } else {
      setProperties([]);
      form.setValue('ga_property_id', '');
    }
  }, [selectedClientId]);

  const loadClients = async () => {
    try {
      setLoadingClients(true);
      const response = await typeSafeApiClient.getClients(1, 100);
      setClients(response.items);
    } catch (error) {
      toast({
        title: '클라이언트 로드 실패',
        description: '클라이언트 목록을 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoadingClients(false);
    }
  };

  const loadProperties = async (clientId: number) => {
    try {
      setLoadingProperties(true);
      const properties = await typeSafeApiClient.getClientProperties(clientId);
      setProperties(properties);
    } catch (error) {
      toast({
        title: 'GA4 속성 로드 실패',
        description: '해당 클라이언트의 GA4 속성을 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
      setProperties([]);
    } finally {
      setLoadingProperties(false);
    }
  };

  const loadAutoApprovalRules = async () => {
    try {
      const response = await typeSafeApiClient.request<{
        rules: AutoApprovalRule[];
        user_role: UserRole;
      }>('/api/permission-requests/auto-approval-rules');
      setAutoApprovalRules(response.rules);
    } catch (error) {
      console.warn('Failed to load auto-approval rules:', error);
    }
  };

  const getApprovalInfo = (permissionLevel: PermissionLevel) => {
    const rule = autoApprovalRules.find(r => r.permission_level === permissionLevel);
    if (!rule) return null;

    if (rule.auto_approved) {
      return {
        type: 'auto',
        message: '자동 승인됩니다',
        icon: CheckCircle,
        color: 'text-green-600'
      };
    } else {
      return {
        type: 'manual',
        message: `${rule.requires_approval_from_role} 승인 필요`,
        icon: Clock,
        color: 'text-yellow-600'
      };
    }
  };

  const onSubmit = async (data: PermissionRequestFormData) => {
    try {
      setSubmitting(true);
      
      const response = await typeSafeApiClient.request<{
        id: number;
        status: string;
        auto_approved: boolean;
      }>('/api/permission-requests/', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const approvalInfo = getApprovalInfo(data.permission_level);
      
      toast({
        title: '권한 요청 완료',
        description: response.auto_approved 
          ? '요청이 자동으로 승인되었습니다.' 
          : `요청이 제출되었습니다. ${approvalInfo?.message || '승인 대기 중입니다.'}`,
      });

      setOpen(false);
      form.reset();
      onSuccess?.(response.id);
    } catch (error: any) {
      toast({
        title: '권한 요청 실패',
        description: error.message || '권한 요청 중 오류가 발생했습니다.',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    setOpen(false);
    form.reset();
    onCancel?.();
  };

  const defaultTrigger = (
    <Button>
      <FileText className="h-4 w-4 mr-2" />
      권한 요청
    </Button>
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 korean-text">
            <Shield className="h-5 w-5" />
            GA4 권한 요청
          </DialogTitle>
          <DialogDescription className="korean-text">
            Google Analytics 4 속성에 대한 접근 권한을 요청합니다.
            요청 내용을 정확히 입력해주세요.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Client Selection */}
            <FormField
              control={form.control}
              name="client_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="korean-text">클라이언트 *</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(parseInt(value))}
                    disabled={loadingClients}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="클라이언트를 선택하세요" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {clients.map((client) => (
                        <SelectItem key={client.id} value={client.id.toString()}>
                          <div className="flex flex-col">
                            <span className="font-medium korean-text">{client.name}</span>
                            <span className="text-sm text-gray-500">{client.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* GA4 Property Selection */}
            <FormField
              control={form.control}
              name="ga_property_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="korean-text">GA4 속성 *</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    disabled={!selectedClientId || loadingProperties}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={
                          !selectedClientId 
                            ? "먼저 클라이언트를 선택하세요"
                            : loadingProperties
                            ? "속성 로딩 중..."
                            : "GA4 속성을 선택하세요"
                        } />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {properties.map((property) => (
                        <SelectItem key={property.property_id} value={property.property_id}>
                          <div className="flex flex-col">
                            <span className="font-medium korean-text">{property.display_name}</span>
                            <span className="text-sm text-gray-500 font-mono">
                              {property.property_id}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    선택한 클라이언트에서 관리하는 GA4 속성입니다.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Target Email */}
            <FormField
              control={form.control}
              name="target_email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="korean-text">대상 이메일 *</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="권한을 부여받을 이메일 주소"
                      {...field}
                      className="korean-text"
                    />
                  </FormControl>
                  <FormDescription>
                    GA4 속성에 접근할 Google 계정 이메일을 입력하세요.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Permission Level */}
            <FormField
              control={form.control}
              name="permission_level"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="korean-text">권한 레벨 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="권한 레벨을 선택하세요" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PERMISSION_LEVELS.map((level) => (
                        <SelectItem key={level.value} value={level.value}>
                          <div className="flex flex-col">
                            <span className="font-medium korean-text">{level.label}</span>
                            <span className="text-sm text-gray-500">{level.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Auto-approval Info */}
            {selectedPermissionLevel && autoApprovalRules.length > 0 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  {(() => {
                    const approvalInfo = getApprovalInfo(selectedPermissionLevel);
                    if (!approvalInfo) return null;
                    
                    const Icon = approvalInfo.icon;
                    return (
                      <div className="flex items-center gap-2">
                        <Icon className={`h-4 w-4 ${approvalInfo.color}`} />
                        <span className="korean-text">{approvalInfo.message}</span>
                      </div>
                    );
                  })()}
                </AlertDescription>
              </Alert>
            )}

            {/* Duration */}
            <FormField
              control={form.control}
              name="requested_duration_days"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="korean-text">요청 기간 (일) *</FormLabel>
                  <FormControl>
                    <Input 
                      type="number"
                      min="1"
                      max="365"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 30)}
                    />
                  </FormControl>
                  <FormDescription>
                    권한을 요청하는 기간입니다. (1일 ~ 365일)
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Business Justification */}
            <FormField
              control={form.control}
              name="business_justification"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="korean-text">업무 사유 *</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="권한이 필요한 구체적인 업무 사유를 입력하세요..."
                      className="min-h-[100px] korean-text"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    권한 요청 사유를 상세히 작성해주세요. (10자 이상 500자 이하)
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={submitting}
              >
                취소
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    요청 중...
                  </>
                ) : (
                  '권한 요청'
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}