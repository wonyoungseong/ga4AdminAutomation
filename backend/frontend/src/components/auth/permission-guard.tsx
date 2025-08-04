'use client';

import React, { ReactNode } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { UserRole } from '@/types/auth';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ShieldX } from 'lucide-react';

interface PermissionGuardProps {
  children: ReactNode;
  requiredPermissions?: string | string[];
  requiredRoles?: UserRole | UserRole[];
  fallback?: ReactNode;
  showFallback?: boolean;
}

/**
 * Permission Guard Component
 * Conditionally renders children based on user permissions or roles
 */
export function PermissionGuard({
  children,
  requiredPermissions,
  requiredRoles,
  fallback,
  showFallback = true,
}: PermissionGuardProps) {
  const { user, hasRole, hasPermission } = useAuth();

  // If user is not authenticated, don't show anything
  if (!user) {
    return null;
  }

  // Check role-based access
  if (requiredRoles) {
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
    if (!hasRole(roles)) {
      return showFallback ? (fallback || <DefaultFallback />) : null;
    }
  }

  // Check permission-based access
  if (requiredPermissions) {
    const permissions = Array.isArray(requiredPermissions) 
      ? requiredPermissions 
      : [requiredPermissions];
    
    const hasAccess = permissions.some(permission => hasPermission(permission));
    if (!hasAccess) {
      return showFallback ? (fallback || <DefaultFallback />) : null;
    }
  }

  return <>{children}</>;
}

/**
 * Default fallback component for permission denied
 */
function DefaultFallback() {
  return (
    <Alert variant="destructive" className="max-w-md">
      <ShieldX className="h-4 w-4" />
      <AlertDescription>
        You don't have permission to access this content.
      </AlertDescription>
    </Alert>
  );
}

/**
 * Role Guard - simplified version for role-based access
 */
interface RoleGuardProps {
  children: ReactNode;
  roles: UserRole | UserRole[];
  fallback?: ReactNode;
  showFallback?: boolean;
}

export function RoleGuard({ children, roles, fallback, showFallback = true }: RoleGuardProps) {
  return (
    <PermissionGuard
      requiredRoles={roles}
      fallback={fallback}
      showFallback={showFallback}
    >
      {children}
    </PermissionGuard>
  );
}

/**
 * Admin Guard - shortcut for admin-only content
 */
interface AdminGuardProps {
  children: ReactNode;
  includeSuper?: boolean;
  fallback?: ReactNode;
  showFallback?: boolean;
}

export function AdminGuard({ 
  children, 
  includeSuper = true, 
  fallback, 
  showFallback = true 
}: AdminGuardProps) {
  const roles = includeSuper 
    ? [UserRole.ADMIN, UserRole.SUPER_ADMIN] 
    : [UserRole.ADMIN];

  return (
    <RoleGuard roles={roles} fallback={fallback} showFallback={showFallback}>
      {children}
    </RoleGuard>
  );
}

/**
 * Super Admin Guard - for super admin only content
 */
interface SuperAdminGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
  showFallback?: boolean;
}

export function SuperAdminGuard({ children, fallback, showFallback = true }: SuperAdminGuardProps) {
  return (
    <RoleGuard roles={UserRole.SUPER_ADMIN} fallback={fallback} showFallback={showFallback}>
      {children}
    </RoleGuard>
  );
}

/**
 * Higher-order component version of PermissionGuard
 */
export function withPermissionGuard<P extends object>(
  Component: React.ComponentType<P>,
  requiredPermissions?: string | string[],
  requiredRoles?: UserRole | UserRole[]
) {
  return function GuardedComponent(props: P) {
    return (
      <PermissionGuard 
        requiredPermissions={requiredPermissions} 
        requiredRoles={requiredRoles}
      >
        <Component {...props} />
      </PermissionGuard>
    );
  };
}

/**
 * Conditional Button - Button that's only enabled/visible based on permissions
 */
interface ConditionalButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  requiredPermissions?: string | string[];
  requiredRoles?: UserRole | UserRole[];
  hideWhenNoAccess?: boolean;
  children: ReactNode;
}

export function ConditionalButton({
  requiredPermissions,
  requiredRoles,
  hideWhenNoAccess = false,
  children,
  disabled,
  ...props
}: ConditionalButtonProps) {
  const { user, hasRole, hasPermission } = useAuth();

  if (!user) {
    return hideWhenNoAccess ? null : (
      <button {...props} disabled={true}>
        {children}
      </button>
    );
  }

  let hasAccess = true;

  // Check role-based access
  if (requiredRoles) {
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
    hasAccess = hasAccess && hasRole(roles);
  }

  // Check permission-based access
  if (requiredPermissions) {
    const permissions = Array.isArray(requiredPermissions) 
      ? requiredPermissions 
      : [requiredPermissions];
    hasAccess = hasAccess && permissions.some(permission => hasPermission(permission));
  }

  if (!hasAccess && hideWhenNoAccess) {
    return null;
  }

  return (
    <button {...props} disabled={disabled || !hasAccess}>
      {children}
    </button>
  );
}