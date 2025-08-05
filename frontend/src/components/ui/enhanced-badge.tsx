"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Badge } from "./badge";

const enhancedBadgeVariants = cva(
  "inline-flex items-center gap-1 korean-text transition-all duration-200",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        success: "border-transparent bg-green-500 text-white hover:bg-green-600",
        warning: "border-transparent bg-yellow-500 text-white hover:bg-yellow-600",
        info: "border-transparent bg-blue-500 text-white hover:bg-blue-600",
      },
      size: {
        sm: "px-2 py-1 text-xs h-5",
        md: "px-2.5 py-1 text-sm h-6",
        lg: "px-3 py-1.5 text-sm h-7",
      },
      interactive: {
        true: "cursor-pointer hover:scale-105 active:scale-95",
        false: ""
      }
    },
    defaultVariants: {
      variant: "default",
      size: "md",
      interactive: false
    },
  }
);

export interface EnhancedBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof enhancedBadgeVariants> {
  icon?: React.ReactNode;
  onRemove?: () => void;
  pulse?: boolean;
}

const EnhancedBadge = React.forwardRef<HTMLDivElement, EnhancedBadgeProps>(
  ({ 
    className, 
    variant, 
    size, 
    interactive, 
    icon, 
    onRemove, 
    pulse = false, 
    children, 
    onClick,
    ...props 
  }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          enhancedBadgeVariants({ variant, size, interactive: interactive || !!onClick }),
          pulse && "animate-pulse",
          className
        )}
        onClick={onClick}
        {...props}
      >
        {icon && <span className="flex-shrink-0">{icon}</span>}
        <span className="truncate">{children}</span>
        {onRemove && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="ml-1 rounded-full hover:bg-black/20 p-0.5 transition-colors"
            aria-label="제거"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M9 3L3 9M3 3l6 6" />
            </svg>
          </button>
        )}
      </div>
    );
  }
);
EnhancedBadge.displayName = "EnhancedBadge";

// Status-specific badge components
const StatusBadge: React.FC<{
  status: 'active' | 'inactive' | 'pending' | 'error' | 'success';
  children: React.ReactNode;
  className?: string;
}> = ({ status, children, className }) => {
  const statusConfig = {
    active: { variant: 'success' as const, pulse: false },
    inactive: { variant: 'secondary' as const, pulse: false },
    pending: { variant: 'warning' as const, pulse: true },
    error: { variant: 'destructive' as const, pulse: false },
    success: { variant: 'success' as const, pulse: false }
  };

  const config = statusConfig[status];

  return (
    <EnhancedBadge
      variant={config.variant}
      pulse={config.pulse}
      className={className}
    >
      {children}
    </EnhancedBadge>
  );
};

// Role-specific badge component
const RoleBadge: React.FC<{
  role: 'super_admin' | 'admin' | 'manager' | 'requester' | 'viewer';
  className?: string;
}> = ({ role, className }) => {
  const roleConfig = {
    super_admin: { variant: 'destructive' as const, text: '최고 관리자' },
    admin: { variant: 'default' as const, text: '관리자' },
    manager: { variant: 'info' as const, text: '매니저' },
    requester: { variant: 'warning' as const, text: '요청자' },
    viewer: { variant: 'secondary' as const, text: '뷰어' }
  };

  const config = roleConfig[role];

  return (
    <EnhancedBadge
      variant={config.variant}
      size="sm"
      className={className}
    >
      {config.text}
    </EnhancedBadge>
  );
};

export { EnhancedBadge, StatusBadge, RoleBadge, enhancedBadgeVariants };