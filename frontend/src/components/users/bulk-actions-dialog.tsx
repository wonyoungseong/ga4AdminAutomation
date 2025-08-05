"use client";

import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { User, UserRole, UserStatus } from '@/types/api';
import { RoleBadge } from '@/components/rbac/role-badge';
import { cn } from '@/lib/utils';
import { 
  Users, 
  Shield, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Trash2,
  Loader2,
  UserCheck,
  UserX
} from 'lucide-react';

interface BulkActionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedUsers: User[];
  action: 'approve' | 'suspend' | 'delete' | 'change_role' | 'change_status' | null;
  onConfirm: (action: string, data?: any) => Promise<void>;
  className?: string;
}

/**
 * Bulk Actions Dialog Component
 * 
 * Handles bulk operations on multiple users with Korean localization
 * and proper confirmation flows for destructive actions
 */
export function BulkActionsDialog({
  open,
  onOpenChange,
  selectedUsers,
  action,
  onConfirm,
  className
}: BulkActionsDialogProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [newRole, setNewRole] = useState<UserRole>('Viewer');
  const [newStatus, setNewStatus] = useState<UserStatus>('active');
  const [reason, setReason] = useState('');

  const handleConfirm = useCallback(async () => {
    if (!action) return;

    setIsProcessing(true);
    try {
      let actionData: any = {};

      switch (action) {
        case 'change_role':
          actionData = { role: newRole, reason };
          break;
        case 'change_status':
          actionData = { status: newStatus, reason };
          break;
        case 'suspend':
          actionData = { reason };
          break;
        case 'delete':
          actionData = { reason };
          break;
        case 'approve':
          actionData = { reason };
          break;
      }

      await onConfirm(action, actionData);
      onOpenChange(false);
      
      // Reset form
      setNewRole('Viewer');
      setNewStatus('active');
      setReason('');
    } catch (error) {
      console.error('Bulk action error:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [action, newRole, newStatus, reason, onConfirm, onOpenChange]);

  // Action configurations
  const actionConfigs = {
    approve: {
      title: '사용자 승인',
      description: '선택한 사용자들을 승인하시겠습니까?',
      icon: <CheckCircle className="h-5 w-5 text-green-600" />,
      buttonText: '승인',
      buttonVariant: 'default' as const,
      destructive: false,
    },
    suspend: {
      title: '사용자 정지',
      description: '선택한 사용자들을 정지하시겠습니까?',
      icon: <UserX className="h-5 w-5 text-orange-600" />,
      buttonText: '정지',
      buttonVariant: 'destructive' as const,
      destructive: true,
    },
    delete: {
      title: '사용자 삭제',
      description: '선택한 사용자들을 영구적으로 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
      icon: <Trash2 className="h-5 w-5 text-red-600" />,
      buttonText: '삭제',
      buttonVariant: 'destructive' as const,
      destructive: true,
    },
    change_role: {
      title: '역할 변경',
      description: '선택한 사용자들의 역할을 변경하시겠습니까?',
      icon: <Shield className="h-5 w-5 text-blue-600" />,
      buttonText: '역할 변경',
      buttonVariant: 'default' as const,
      destructive: false,
    },
    change_status: {
      title: '상태 변경',
      description: '선택한 사용자들의 상태를 변경하시겠습니까?',
      icon: <AlertTriangle className="h-5 w-5 text-yellow-600" />,
      buttonText: '상태 변경',
      buttonVariant: 'default' as const,
      destructive: false,
    },
  };

  const config = action ? actionConfigs[action] : null;

  if (!config || selectedUsers.length === 0) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('max-w-2xl', className)}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 korean-text">
            {config.icon}
            {config.title}
          </DialogTitle>
          <DialogDescription className="korean-text">
            {config.description}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Selected Users Preview */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-3">
                <Users className="h-4 w-4" />
                <span className="font-medium korean-text">
                  선택된 사용자 ({selectedUsers.length}명)
                </span>
              </div>
              <div className="max-h-32 overflow-y-auto space-y-2">
                {selectedUsers.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                    <div className="flex items-center gap-2">
                      <span className="font-medium korean-text">{user.name}</span>
                      <span className="text-sm text-gray-500">{user.email}</span>
                    </div>
                    <RoleBadge role={user.role} status={user.status} size="sm" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Action-specific Fields */}
          {action === 'change_role' && (
            <div className="space-y-3">
              <Label className="korean-text">새 역할</Label>
              <Select value={newRole} onValueChange={(value) => setNewRole(value as UserRole)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Super Admin">
                    <div className="flex items-center gap-2">
                      <RoleBadge role="Super Admin" size="sm" />
                    </div>
                  </SelectItem>
                  <SelectItem value="Admin">
                    <div className="flex items-center gap-2">
                      <RoleBadge role="Admin" size="sm" />
                    </div>
                  </SelectItem>
                  <SelectItem value="Requester">
                    <div className="flex items-center gap-2">
                      <RoleBadge role="Requester" size="sm" />
                    </div>
                  </SelectItem>
                  <SelectItem value="Viewer">
                    <div className="flex items-center gap-2">
                      <RoleBadge role="Viewer" size="sm" />
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-gray-600 dark:text-gray-400 korean-text">
                선택한 모든 사용자의 역할이 "{newRole}"로 변경됩니다.
              </p>
            </div>
          )}

          {action === 'change_status' && (
            <div className="space-y-3">
              <Label className="korean-text">새 상태</Label>
              <Select value={newStatus} onValueChange={(value) => setNewStatus(value as UserStatus)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="korean-text">활성</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="inactive">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-gray-600" />
                      <span className="korean-text">비활성</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="suspended">
                    <div className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <span className="korean-text">정지됨</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Reason Field */}
          {(config.destructive || action === 'suspend' || action === 'change_role') && (
            <div className="space-y-3">
              <Label className="korean-text">
                {action === 'change_role' ? '변경 사유' : '처리 사유'}
                {config.destructive && ' *'}
              </Label>
              <Textarea
                placeholder={
                  action === 'delete' 
                    ? '삭제 사유를 입력해주세요...'
                    : action === 'suspend'
                    ? '정지 사유를 입력해주세요...'
                    : '변경 사유를 입력해주세요...'
                }
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="min-h-[80px] korean-text"
                required={config.destructive}
              />
              {config.destructive && (
                <p className="text-sm text-red-600 korean-text">
                  이 작업은 되돌릴 수 없으므로 사유를 반드시 입력해주세요.
                </p>
              )}
            </div>
          )}

          {/* Warning for destructive actions */}
          {config.destructive && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium korean-text">주의</span>
              </div>
              <p className="text-sm text-red-700 dark:text-red-300 mt-2 korean-text">
                {action === 'delete' 
                  ? '이 작업을 수행하면 선택한 사용자들의 모든 데이터가 영구적으로 삭제됩니다.'
                  : '이 작업을 수행하면 선택한 사용자들이 시스템에 접근할 수 없게 됩니다.'
                }
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isProcessing}
          >
            취소
          </Button>
          <Button
            variant={config.buttonVariant}
            onClick={handleConfirm}
            disabled={isProcessing || (config.destructive && !reason.trim())}
          >
            {isProcessing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {config.buttonText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}