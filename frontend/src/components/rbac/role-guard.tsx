"use client";

import React from 'react';
import { useAuth } from '@/contexts/auth-context';
import { UserRole } from '@/types/api';

interface RoleGuardProps {
  allowedRoles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requireAll?: boolean;
}

/**
 * RBAC Role Guard Component
 * 
 * Guards content based on user roles with Korean support
 * Synchronized with Backend RBAC implementation
 */
export function RoleGuard({ 
  allowedRoles, 
  children, 
  fallback = null,
  requireAll = false 
}: RoleGuardProps) {
  const { user, isLoading } = useAuth();

  // Loading state
  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  // No user - deny access
  if (!user) {
    return fallback ? <>{fallback}</> : null;
  }

  // Check role permissions
  const hasPermission = requireAll 
    ? allowedRoles.every(role => user.role === role)
    : allowedRoles.includes(user.role);

  if (!hasPermission) {
    return fallback ? <>{fallback}</> : null;
  }

  return <>{children}</>;
}

/**
 * Role-based conditional rendering hook
 */
export function useRoleCheck(allowedRoles: UserRole[]): boolean {
  const { user } = useAuth();
  
  if (!user) return false;
  
  return allowedRoles.includes(user.role);
}

/**
 * Korean localized unauthorized message
 */
export function UnauthorizedMessage() {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="text-4xl mb-4">🔒</div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        접근 권한이 없습니다
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        이 기능을 사용하려면 적절한 권한이 필요합니다.
      </p>
    </div>
  );
}

/**
 * Permission level guard for granular access control
 */
interface PermissionGuardProps {
  permission: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGuard({ 
  permission, 
  children, 
  fallback = <UnauthorizedMessage /> 
}: PermissionGuardProps) {
  const { user } = useAuth();

  if (!user) {
    return fallback ? <>{fallback}</> : null;
  }

  // Check specific permissions based on role hierarchy
  const hasPermission = checkPermission(user.role, permission);

  return hasPermission ? <>{children}</> : fallback ? <>{fallback}</> : null;
}

/**
 * Role hierarchy and permission checker
 */
function checkPermission(userRole: UserRole, permission: string): boolean {
  // Role hierarchy (highest to lowest)
  const roleHierarchy: Record<UserRole, number> = {
    'Super Admin': 4,
    'Admin': 3,
    'Requester': 2,
    'Viewer': 1
  };

  // Permission requirements
  const permissionRequirements: Record<string, number> = {
    'user.create': 3,       // Admin+
    'user.edit': 3,         // Admin+
    'user.delete': 4,       // Super Admin only
    'user.approve': 3,      // Admin+
    'permission.grant': 3,  // Admin+
    'permission.revoke': 3, // Admin+
    'audit.view': 2,        // Requester+
    'dashboard.admin': 3,   // Admin+
    'system.config': 4,     // Super Admin only
  };

  const userLevel = roleHierarchy[userRole] || 0;
  const requiredLevel = permissionRequirements[permission] || 1;

  return userLevel >= requiredLevel;
}