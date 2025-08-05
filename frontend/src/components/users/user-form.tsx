"use client";

import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { User, UserRole, UserStatus, UserCreate, UserUpdate } from '@/types/api';
import { RoleBadge } from '@/components/rbac/role-badge';
import { RoleGuard } from '@/components/rbac/role-guard';
import { useAuth } from '@/contexts/auth-context';
import { cn } from '@/lib/utils';
import { 
  User as UserIcon,
  Mail, 
  Phone, 
  Building, 
  Briefcase,
  Users,
  Shield,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';

// Korean validation schema
const koreanPhoneRegex = /^(010|011|016|017|018|019)-?\d{3,4}-?\d{4}$/;
const koreanBusinessNumberRegex = /^\d{3}-?\d{2}-?\d{5}$/;

const userFormSchema = z.object({
  name: z.string()
    .min(2, '이름은 2글자 이상이어야 합니다')
    .max(50, '이름은 50글자를 넘을 수 없습니다')
    .regex(/^[가-힣a-zA-Z\s]+$/, '이름은 한글 또는 영문만 입력 가능합니다'),
  email: z.string()
    .email('올바른 이메일 주소를 입력해주세요')
    .max(100, '이메일은 100글자를 넘을 수 없습니다'),
  company: z.string()
    .min(2, '회사명은 2글자 이상이어야 합니다')
    .max(100, '회사명은 100글자를 넘을 수 없습니다')
    .optional()
    .or(z.literal('')),
  department: z.string()
    .max(50, '부서명은 50글자를 넘을 수 없습니다')
    .optional()
    .or(z.literal('')),
  job_title: z.string()
    .max(50, '직책은 50글자를 넘을 수 없습니다')
    .optional()
    .or(z.literal('')),
  phone_number: z.string()
    .regex(koreanPhoneRegex, '올바른 한국 휴대폰 번호를 입력해주세요 (예: 010-1234-5678)')
    .optional()
    .or(z.literal('')),
  role: z.enum(['Super Admin', 'Admin', 'Requester', 'Viewer'] as const),
  status: z.enum(['active', 'inactive', 'suspended'] as const),
  is_representative: z.boolean().optional(),
  primary_client_id: z.number().optional(),
});

type UserFormData = z.infer<typeof userFormSchema>;

interface UserFormProps {
  user?: User;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: UserCreate | UserUpdate) => Promise<void>;
  mode: 'create' | 'edit';
  className?: string;
}

/**
 * User Creation/Edit Form Component
 * 
 * Comprehensive user form with Korean validation,
 * RBAC role assignment, and business field validation
 */
export function UserForm({
  user,
  open,
  onOpenChange,
  onSubmit,
  mode,
  className
}: UserFormProps) {
  const { user: currentUser } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<UserFormData>({
    resolver: zodResolver(userFormSchema),
    defaultValues: {
      name: user?.name || '',
      email: user?.email || '',
      company: user?.company || '',
      department: user?.department || '',
      job_title: user?.job_title || '',
      phone_number: user?.phone_number || '',
      role: user?.role || 'Viewer',
      status: user?.status || 'active',
      is_representative: user?.is_representative || false,
      primary_client_id: user?.primary_client_id,
    },
  });

  const handleSubmit = useCallback(async (data: UserFormData) => {
    setIsSubmitting(true);
    try {
      // Clean up empty strings to undefined
      const cleanedData = {
        ...data,
        company: data.company || undefined,
        department: data.department || undefined,
        job_title: data.job_title || undefined,
        phone_number: data.phone_number || undefined,
      };

      await onSubmit(cleanedData);
      onOpenChange(false);
      form.reset();
    } catch (error) {
      console.error('User form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [onSubmit, onOpenChange, form]);

  // Check if current user can assign roles
  const canAssignRole = (targetRole: UserRole): boolean => {
    if (!currentUser) return false;
    
    const roleHierarchy: Record<UserRole, number> = {
      'Super Admin': 4,
      'Admin': 3,
      'Requester': 2,
      'Viewer': 1
    };

    const currentUserLevel = roleHierarchy[currentUser.role] || 0;
    const targetRoleLevel = roleHierarchy[targetRole] || 0;

    // Super Admin can assign any role
    // Admin can assign Requester and Viewer
    // Others cannot assign roles
    return currentUserLevel > targetRoleLevel;
  };

  // Available roles based on current user's permissions
  const availableRoles = React.useMemo(() => {
    const allRoles: UserRole[] = ['Super Admin', 'Admin', 'Requester', 'Viewer'];
    return allRoles.filter(role => canAssignRole(role));
  }, [currentUser]);

  // Role descriptions
  const roleDescriptions: Record<UserRole, string> = {
    'Super Admin': '시스템의 모든 기능에 접근할 수 있는 최고 관리자 권한입니다.',
    'Admin': '사용자 관리, 권한 승인 등 관리 기능에 접근할 수 있습니다.',
    'Requester': 'GA4 속성 접근 권한을 요청할 수 있는 일반 사용자입니다.',
    'Viewer': '승인된 GA4 속성의 데이터를 조회만 할 수 있습니다.'
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('max-w-2xl max-h-[90vh] overflow-y-auto', className)}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 korean-text">
            <UserIcon className="h-5 w-5" />
            {mode === 'create' ? '새 사용자 추가' : '사용자 정보 수정'}
          </DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <UserIcon className="h-4 w-4" />
                  <span className="korean-text">기본 정보</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="korean-text">이름 *</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="홍길동"
                            className="korean-text"
                            {...field} 
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="korean-text">이메일 *</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input 
                              type="email"
                              placeholder="hong@example.com"
                              className="pl-10"
                              disabled={mode === 'edit'}
                              {...field} 
                            />
                          </div>
                        </FormControl>
                        {mode === 'edit' && (
                          <FormDescription className="korean-text">
                            이메일은 수정할 수 없습니다.
                          </FormDescription>
                        )}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="phone_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="korean-text">휴대폰 번호</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <Input 
                            placeholder="010-1234-5678"
                            className="pl-10"
                            {...field} 
                          />
                        </div>
                      </FormControl>
                      <FormDescription className="korean-text">
                        한국 휴대폰 번호 형식으로 입력해주세요.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Company Information */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  <span className="korean-text">회사 정보</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="company"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="korean-text">회사명</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input 
                              placeholder="(주)예시회사"
                              className="pl-10 korean-text"
                              {...field} 
                            />
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="department"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="korean-text">부서</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="마케팅팀"
                            className="korean-text"
                            {...field} 
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="job_title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="korean-text">직책</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Briefcase className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <Input 
                            placeholder="마케팅 매니저"
                            className="pl-10 korean-text"
                            {...field} 
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="is_representative"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <div className="space-y-1 leading-none">
                        <FormLabel className="korean-text">
                          회사 대표자
                        </FormLabel>
                        <FormDescription className="korean-text">
                          이 사용자를 회사의 대표자로 설정합니다.
                        </FormDescription>
                      </div>
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Role and Status */}
            <RoleGuard allowedRoles={['Super Admin', 'Admin']}>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    <span className="korean-text">권한 및 상태</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="role"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="korean-text">역할 *</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="역할을 선택해주세요" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {availableRoles.map((role) => (
                                <SelectItem key={role} value={role}>
                                  <div className="flex items-center gap-2">
                                    <RoleBadge role={role} size="sm" />
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {field.value && (
                            <FormDescription className="korean-text">
                              {roleDescriptions[field.value]}
                            </FormDescription>
                          )}
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="status"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="korean-text">상태</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="상태를 선택해주세요" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="active">
                                <div className="flex items-center gap-2">
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                  <span className="korean-text">활성</span>
                                </div>
                              </SelectItem>
                              <SelectItem value="inactive">
                                <div className="flex items-center gap-2">
                                  <AlertCircle className="h-4 w-4 text-gray-600" />
                                  <span className="korean-text">비활성</span>
                                </div>
                              </SelectItem>
                              <SelectItem value="suspended">
                                <div className="flex items-center gap-2">
                                  <AlertCircle className="h-4 w-4 text-red-600" />
                                  <span className="korean-text">정지됨</span>
                                </div>
                              </SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  {/* Role Preview */}
                  {form.watch('role') && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Shield className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium korean-text">권한 미리보기</span>
                      </div>
                      <RoleBadge role={form.watch('role')} status={form.watch('status')} />
                    </div>
                  )}
                </CardContent>
              </Card>
            </RoleGuard>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                취소
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {mode === 'create' ? '사용자 추가' : '수정 완료'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}