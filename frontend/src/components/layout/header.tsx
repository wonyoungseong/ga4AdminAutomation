"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { usePathname } from "next/navigation";

const pathMap: Record<string, string> = {
  '/dashboard': '대시보드',
  '/dashboard/users': '사용자 관리',
  '/dashboard/permissions': '권한 관리',
  '/dashboard/clients': '클라이언트 관리',
  '/dashboard/audit': '감사 로그',
  '/dashboard/settings': '설정',
  '/dashboard/service-accounts': '서비스 계정 관리',
  '/dashboard/service-accounts/add': '서비스 계정 추가',
  '/dashboard/ga4-properties': 'GA4 Property 관리',
};

export function Header() {
  const pathname = usePathname();
  
  const getCurrentPageTitle = () => {
    return pathMap[pathname] || '대시보드';
  };

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
      <div className="flex items-center gap-2 px-4 w-full">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <div className="flex items-center space-x-2 flex-1">
          <h1 className="text-lg font-semibold text-foreground">
            {getCurrentPageTitle()}
          </h1>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}