"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg";
  variant?: "default" | "overlay";
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  ({ className, size = "md", variant = "default", ...props }, ref) => {
    const sizeClasses = {
      sm: "h-4 w-4",
      md: "h-6 w-6", 
      lg: "h-8 w-8"
    };

    const containerClasses = {
      default: "flex items-center justify-center",
      overlay: "fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
    };

    return (
      <div
        ref={ref}
        className={cn(containerClasses[variant], className)}
        {...props}
      >
        <Loader2 className={cn("animate-spin text-primary", sizeClasses[size])} />
      </div>
    );
  }
);
LoadingSpinner.displayName = "LoadingSpinner";

interface LoadingSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  lines?: number;
  avatar?: boolean;
}

const LoadingSkeleton = React.forwardRef<HTMLDivElement, LoadingSkeletonProps>(
  ({ className, lines = 3, avatar = false, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("animate-pulse space-y-3", className)}
        {...props}
      >
        {avatar && (
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-muted"></div>
            <div className="space-y-2">
              <div className="h-4 w-32 rounded bg-muted"></div>
              <div className="h-3 w-24 rounded bg-muted"></div>
            </div>
          </div>
        )}
        
        <div className="space-y-2">
          {Array.from({ length: lines }).map((_, i) => (
            <div
              key={i}
              className={cn(
                "h-4 rounded bg-muted",
                i === lines - 1 ? "w-3/4" : "w-full"
              )}
            />
          ))}
        </div>
      </div>
    );
  }
);
LoadingSkeleton.displayName = "LoadingSkeleton";

interface LoadingCardProps extends React.HTMLAttributes<HTMLDivElement> {
  showAvatar?: boolean;
  showActions?: boolean;
}

const LoadingCard = React.forwardRef<HTMLDivElement, LoadingCardProps>(
  ({ className, showAvatar = false, showActions = false, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border bg-card p-6 shadow animate-pulse space-y-4",
          className
        )}
        {...props}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-5 w-32 rounded bg-muted"></div>
            <div className="h-4 w-48 rounded bg-muted"></div>
          </div>
          {showAvatar && (
            <div className="h-10 w-10 rounded-full bg-muted"></div>
          )}
        </div>

        {/* Content */}
        <div className="space-y-2">
          <div className="h-4 w-full rounded bg-muted"></div>
          <div className="h-4 w-5/6 rounded bg-muted"></div>
          <div className="h-4 w-4/6 rounded bg-muted"></div>
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2 pt-2">
            <div className="h-9 w-20 rounded bg-muted"></div>
            <div className="h-9 w-16 rounded bg-muted"></div>
          </div>
        )}
      </div>
    );
  }
);
LoadingCard.displayName = "LoadingCard";

interface LoadingPageProps {
  title?: string;
  description?: string;
}

const LoadingPage: React.FC<LoadingPageProps> = ({ 
  title = "로딩 중...", 
  description = "잠시만 기다려 주세요" 
}) => {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="text-center space-y-4">
        <LoadingSpinner size="lg" />
        <div className="space-y-2">
          <h2 className="text-lg font-semibold korean-text">{title}</h2>
          <p className="text-sm text-muted-foreground korean-text">{description}</p>
        </div>
      </div>
    </div>
  );
};

export {
  LoadingSpinner,
  LoadingSkeleton,
  LoadingCard,
  LoadingPage
};