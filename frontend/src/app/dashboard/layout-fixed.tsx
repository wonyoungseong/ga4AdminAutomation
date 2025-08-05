"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, isRefreshing } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [redirectTimer, setRedirectTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Clear any existing redirect timer
    if (redirectTimer) {
      clearTimeout(redirectTimer);
      setRedirectTimer(null);
    }

    // Don't redirect while loading or refreshing tokens
    if (isLoading || isRefreshing) {
      return;
    }

    // If no user after loading is complete and not refreshing, set up delayed redirect
    if (!user) {
      console.log('No user found after auth check, setting up redirect...');
      
      // Give additional time for any ongoing authentication processes
      const timer = setTimeout(() => {
        if (!user && !isRefreshing) {
          console.log('Redirecting to login - no user authenticated');
          // Store the intended destination before redirecting to login
          if (typeof window !== 'undefined') {
            sessionStorage.setItem('redirectAfterLogin', pathname);
          }
          router.push("/login");
        }
      }, 1500); // 1.5 second delay to allow token refresh to complete

      setRedirectTimer(timer);
    }

    // Cleanup timer on unmount or when dependencies change
    return () => {
      if (redirectTimer) {
        clearTimeout(redirectTimer);
      }
    };
  }, [user, isLoading, isRefreshing, router, pathname]);

  // Handle browser back button properly
  useEffect(() => {
    if (typeof window !== 'undefined' && user) {
      const handlePopState = (event: PopStateEvent) => {
        // Prevent going back to login if user is authenticated
        if (window.location.pathname === '/login') {
          event.preventDefault();
          router.push('/dashboard');
        }
      };

      window.addEventListener('popstate', handlePopState);
      return () => window.removeEventListener('popstate', handlePopState);
    }
  }, [user, router]);

  // Replace history state to prevent back button from going to login
  useEffect(() => {
    if (typeof window !== 'undefined' && user) {
      // Replace the current history entry to ensure proper navigation
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [user]);

  // Show loading state while authenticating or refreshing
  if (isLoading || isRefreshing) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">
            {isRefreshing ? '인증 정보 갱신 중...' : '로딩 중...'}
          </p>
        </div>
      </div>
    );
  }

  // Don't render anything if redirecting to login
  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">인증 확인 중...</p>
        </div>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <Header />
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}