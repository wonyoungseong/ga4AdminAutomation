"use client";

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { UserRole, PermissionLevel } from '@/types/api';
import { RoleBadge } from './role-badge';
import { cn } from '@/lib/utils';

/**
 * Permission Matrix Component
 * 
 * Visual matrix for managing role-based permissions
 * Korean-localized with Backend API synchronization
 */

interface PermissionItem {
  id: string;
  name: string;
  description: string;
  category: string;
  requiredRole: UserRole;
}

interface PermissionMatrixProps {
  permissions: PermissionItem[];
  userRole: UserRole;
  onPermissionChange?: (permissionId: string, level: PermissionLevel, enabled: boolean) => void;
  readonly?: boolean;
  className?: string;
}

export function PermissionMatrix({ 
  permissions, 
  userRole, 
  onPermissionChange,
  readonly = false,
  className 
}: PermissionMatrixProps) {
  const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Group permissions by category
  const permissionsByCategory = permissions.reduce((acc, permission) => {
    if (!acc[permission.category]) {
      acc[permission.category] = [];
    }
    acc[permission.category].push(permission);
    return acc;
  }, {} as Record<string, PermissionItem[]>);

  // Korean category labels
  const categoryLabels: Record<string, string> = {
    'user_management': '사용자 관리',
    'permission_management': '권한 관리',
    'ga4_properties': 'GA4 속성',
    'audit_logs': '감사 로그',
    'system_config': '시스템 설정',
    'dashboard': '대시보드'
  };

  // Permission levels
  const permissionLevels: PermissionLevel[] = ['read', 'edit', 'manage'];

  const toggleCategory = useCallback((category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  }, []);

  const handlePermissionToggle = useCallback((permissionId: string, level: PermissionLevel) => {
    if (readonly) return;

    const newSelected = new Set(selectedPermissions);
    const key = `${permissionId}:${level}`;
    
    if (newSelected.has(key)) {
      newSelected.delete(key);
      onPermissionChange?.(permissionId, level, false);
    } else {
      newSelected.add(key);
      onPermissionChange?.(permissionId, level, true);
    }
    
    setSelectedPermissions(newSelected);
  }, [selectedPermissions, readonly, onPermissionChange]);

  // Check if user can access permission
  const canAccessPermission = (permission: PermissionItem): boolean => {
    const roleHierarchy: Record<UserRole, number> = {
      'Super Admin': 4,
      'Admin': 3,
      'Requester': 2,
      'Viewer': 1
    };

    return roleHierarchy[userRole] >= roleHierarchy[permission.requiredRole];
  };

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="korean-text">권한 매트릭스</span>
          <RoleBadge role={userRole} />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Object.entries(permissionsByCategory).map(([category, categoryPermissions]) => (
            <div key={category} className="border rounded-lg">
              <button
                onClick={() => toggleCategory(category)}
                className="w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium korean-text">
                    {categoryLabels[category] || category}
                  </h3>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {categoryPermissions.length}개 권한
                    </Badge>
                    <span className="text-gray-400">
                      {expandedCategories.has(category) ? '▼' : '▶'}
                    </span>
                  </div>
                </div>
              </button>
              
              {expandedCategories.has(category) && (
                <div className="border-t bg-gray-50 dark:bg-gray-900/50">
                  <div className="p-4">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2 korean-text">권한명</th>
                            <th className="text-left p-2 korean-text">설명</th>
                            {permissionLevels.map(level => (
                              <th key={level} className="text-center p-2 korean-text">
                                {getPermissionLevelLabel(level)}
                              </th>
                            ))}
                            <th className="text-center p-2 korean-text">필요 역할</th>
                          </tr>
                        </thead>
                        <tbody>
                          {categoryPermissions.map(permission => (
                            <tr key={permission.id} className="border-b hover:bg-white dark:hover:bg-gray-800">
                              <td className="p-2 font-medium korean-text">
                                {permission.name}
                              </td>
                              <td className="p-2 text-gray-600 dark:text-gray-400 korean-text">
                                {permission.description}
                              </td>
                              {permissionLevels.map(level => (
                                <td key={level} className="p-2 text-center">
                                  <Checkbox
                                    checked={selectedPermissions.has(`${permission.id}:${level}`)}
                                    onCheckedChange={() => handlePermissionToggle(permission.id, level)}
                                    disabled={readonly || !canAccessPermission(permission)}
                                    className="mx-auto"
                                  />
                                </td>
                              ))}
                              <td className="p-2 text-center">
                                <RoleBadge role={permission.requiredRole} size="sm" />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {!readonly && (
          <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
            <Button variant="outline" onClick={() => setSelectedPermissions(new Set())}>
              초기화
            </Button>
            <Button onClick={() => console.log('Save permissions', selectedPermissions)}>
              권한 저장
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact Permission Summary Component
 */
interface PermissionSummaryProps {
  userRole: UserRole;
  permissions: string[];
  className?: string;
}

export function PermissionSummary({ userRole, permissions, className }: PermissionSummaryProps) {
  return (
    <Card className={cn('p-4', className)}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium korean-text">권한 요약</h4>
        <RoleBadge role={userRole} size="sm" />
      </div>
      <div className="flex flex-wrap gap-1">
        {permissions.slice(0, 6).map((permission, index) => (
          <Badge key={index} variant="outline" className="text-xs korean-text">
            {permission}
          </Badge>
        ))}
        {permissions.length > 6 && (
          <Badge variant="outline" className="text-xs">
            +{permissions.length - 6}개 더
          </Badge>
        )}
      </div>
    </Card>
  );
}

// Helper Functions
function getPermissionLevelLabel(level: PermissionLevel): string {
  const labels = {
    read: '읽기',
    edit: '편집',
    manage: '관리'
  };
  return labels[level];
}