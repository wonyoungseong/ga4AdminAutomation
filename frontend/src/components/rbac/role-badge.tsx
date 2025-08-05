"use client";

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { UserRole, UserStatus } from '@/types/api';
import { cn } from '@/lib/utils';

interface RoleBadgeProps {
  role: UserRole;
  status?: UserStatus;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * RBAC Role Badge Component
 * 
 * Displays user roles with Korean labels and status indicators
 * Synchronized with Backend RBAC role definitions
 */
export function RoleBadge({ role, status, size = 'md', className }: RoleBadgeProps) {
  // Korean role labels
  const roleLabels: Record<UserRole, string> = {
    'Super Admin': '최고 관리자',
    'Admin': '관리자',
    'Requester': '요청자',
    'Viewer': '뷰어'
  };

  // Role-based styling
  const roleStyles: Record<UserRole, string> = {
    'Super Admin': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-200',
    'Admin': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 border-orange-200',
    'Requester': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-200',
    'Viewer': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200 border-gray-200'
  };

  // Status styling
  const statusStyles: Record<UserStatus, string> = {
    'active': 'ring-2 ring-green-200 dark:ring-green-800',
    'inactive': 'ring-2 ring-gray-200 dark:ring-gray-800 opacity-60',
    'suspended': 'ring-2 ring-red-200 dark:ring-red-800 opacity-75'
  };

  // Size styling
  const sizeStyles = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  };

  return (
    <Badge 
      className={cn(
        'inline-flex items-center font-medium border transition-all duration-200',
        roleStyles[role],
        status && statusStyles[status],
        sizeStyles[size],
        className
      )}
      title={`역할: ${roleLabels[role]}${status ? ` (${getStatusLabel(status)})` : ''}`}
    >
      {getRoleIcon(role)}
      <span className="ml-1 korean-text">{roleLabels[role]}</span>
      {status && status !== 'active' && (
        <span className="ml-1 text-xs opacity-75">
          • {getStatusLabel(status)}
        </span>
      )}
    </Badge>
  );
}

/**
 * Role Permission Level Badge
 */
interface PermissionBadgeProps {
  permission: string;
  level?: 'read' | 'edit' | 'manage';
  className?: string;
}

export function PermissionBadge({ permission, level = 'read', className }: PermissionBadgeProps) {
  const levelLabels = {
    read: '읽기',
    edit: '편집',
    manage: '관리'
  };

  const levelStyles = {
    read: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    edit: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    manage: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
  };

  return (
    <Badge 
      className={cn(
        'inline-flex items-center font-medium',
        levelStyles[level],
        className
      )}
      title={`권한: ${permission} (${levelLabels[level]})`}
    >
      {getPermissionIcon(level)}
      <span className="ml-1 korean-text">{levelLabels[level]}</span>
    </Badge>
  );
}

/**
 * Multi-Role Display Component
 */
interface MultiRoleBadgeProps {
  roles: UserRole[];
  maxDisplay?: number;
  className?: string;
}

export function MultiRoleBadge({ roles, maxDisplay = 2, className }: MultiRoleBadgeProps) {
  const displayRoles = roles.slice(0, maxDisplay);
  const remainingCount = roles.length - maxDisplay;

  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      {displayRoles.map((role, index) => (
        <RoleBadge key={`${role}-${index}`} role={role} size="sm" />
      ))}
      {remainingCount > 0 && (
        <Badge className="text-xs bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
          +{remainingCount}개 더
        </Badge>
      )}
    </div>
  );
}

// Helper Functions
function getRoleIcon(role: UserRole): React.ReactNode {
  const icons = {
    'Super Admin': '👑',
    'Admin': '🛡️',
    'Requester': '👤',
    'Viewer': '👁️'
  };
  return <span className="text-xs">{icons[role]}</span>;
}

function getPermissionIcon(level: 'read' | 'edit' | 'manage'): React.ReactNode {
  const icons = {
    read: '👁️',
    edit: '✏️',
    manage: '⚙️'
  };
  return <span className="text-xs">{icons[level]}</span>;
}

function getStatusLabel(status: UserStatus): string {
  const labels = {
    active: '활성',
    inactive: '비활성',
    suspended: '정지됨'
  };
  return labels[status];
}