"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { usePathname } from "next/navigation";

const pathMap: Record<string, string> = {
  '/dashboard': '대시보드',
  '/dashboard/users': '사용자 관리',
  '/dashboard/permissions': '권한 관리',
  '/dashboard/clients': '클라이언트 관리',
  '/dashboard/audit': '감사 로그',
  '/dashboard/settings': '설정',
};

export function Header() {
  const pathname = usePathname();
  
  const getBreadcrumbs = () => {
    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs = [];
    
    // 루트 대시보드는 항상 포함
    breadcrumbs.push({
      href: '/dashboard',
      label: '대시보드',
      isLast: pathname === '/dashboard'
    });
    
    // 현재 페이지가 대시보드가 아닌 경우 추가
    if (pathname !== '/dashboard') {
      const currentPath = pathname;
      const currentLabel = pathMap[currentPath] || segments[segments.length - 1];
      
      breadcrumbs.push({
        href: currentPath,
        label: currentLabel,
        isLast: true
      });
    }
    
    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            {breadcrumbs.map((breadcrumb, index) => (
              <div key={breadcrumb.href} className="flex items-center">
                {index > 0 && <BreadcrumbSeparator className="mx-2" />}
                <BreadcrumbItem>
                  {breadcrumb.isLast ? (
                    <BreadcrumbPage>{breadcrumb.label}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink href={breadcrumb.href}>
                      {breadcrumb.label}
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
              </div>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
  );
}