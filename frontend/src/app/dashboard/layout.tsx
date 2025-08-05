"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";
import { AuthDebug } from "@/components/debug/auth-debug";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, isInitialized, isRefreshing } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    console.log('[DashboardLayout] Auth state changed:', {
      isLoading, 
      isInitialized, 
      isRefreshing, 
      user: user ? user.email : 'null', 
      pathname
    });
    
    // Only redirect if:
    // 1. Auth is fully initialized (not loading and not refreshing)
    // 2. No user is present
    // 3. We're not in the middle of a token refresh
    if (isInitialized && !isLoading && !isRefreshing && !user) {
      console.log('[DashboardLayout] Auth fully initialized with no user, setting up redirect');
      
      // Give a small delay to account for any last-moment state changes
      const redirectTimer = setTimeout(() => {
        // Double-check the conditions haven't changed
        if (!user && !isRefreshing) {
          console.log('[DashboardLayout] Redirecting to login after final check');
          // Store the intended destination before redirecting to login
          if (typeof window !== 'undefined') {
            sessionStorage.setItem('redirectAfterLogin', pathname);
          }
          router.push("/login");
        }
      }, 200); // Shorter delay since we're now more confident in our state

      return () => clearTimeout(redirectTimer);
    }
  }, [user, isLoading, isInitialized, isRefreshing, router, pathname]);

  // Handle browser back button properly
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const handlePopState = (event: PopStateEvent) => {
        // Prevent going back to login if user is authenticated
        if (user && window.location.pathname === '/login') {
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

  // Show loading state while auth is being initialized or refreshed
  if (isLoading || !isInitialized || isRefreshing) {
    const loadingMessage = isRefreshing ? '인증 갱신 중...' : '로딩 중...';
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  // If auth is initialized but no user, show nothing (redirect will happen)
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
      <AuthDebug />
    </SidebarProvider>
  );
}