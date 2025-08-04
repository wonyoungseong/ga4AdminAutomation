'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Users, 
  Building2, 
  Key, 
  Shield, 
  FileText, 
  User,
  Settings,
  LogOut,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { NavigationItems, NavItem, UserRole } from '@/types/auth';
import { cn, snakeToTitle } from '@/lib/utils';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { PermissionGuard } from '@/components/auth/permission-guard';

const iconMap: Record<string, React.ComponentType<any>> = {
  LayoutDashboard,
  Users,
  Building2,
  Key,
  Shield,
  FileText,
  User,
  Settings,
};

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const { user, logout, hasPermission } = useAuth();
  const pathname = usePathname();

  if (!user) return null;

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getRoleColor = (role: UserRole) => {
    const colors = {
      [UserRole.SUPER_ADMIN]: 'bg-red-100 text-red-800',
      [UserRole.ADMIN]: 'bg-orange-100 text-orange-800',
      [UserRole.REQUESTER]: 'bg-blue-100 text-blue-800',
      [UserRole.GA_USER]: 'bg-green-100 text-green-800',
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className={cn("flex h-full w-64 flex-col bg-white border-r", className)}>
      {/* Header */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="font-semibold">GA4 Admin</div>
        </Link>
      </div>

      {/* User Info */}
      <div className="border-b p-4">
        <div className="flex items-center space-x-3">
          <Avatar className="h-10 w-10">
            <AvatarImage src="" alt={user.name} />
            <AvatarFallback className="bg-primary text-primary-foreground">
              {getInitials(user.name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user.name}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {user.email}
            </p>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-between">
          <Badge className={cn("text-xs", getRoleColor(user.role))}>
            {snakeToTitle(user.role)}
          </Badge>
          {user.company && (
            <span className="text-xs text-gray-500 truncate ml-2">
              {user.company}
            </span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {NavigationItems.map((item) => (
            <NavItemComponent
              key={item.href}
              item={item}
              currentPath={pathname}
              hasPermission={hasPermission}
            />
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t p-4">
        <Button
          variant="ghost"
          className="w-full justify-start"
          onClick={handleLogout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}

interface NavItemComponentProps {
  item: NavItem;
  currentPath: string;
  hasPermission: (permission: string) => boolean;
  level?: number;
}

function NavItemComponent({ 
  item, 
  currentPath, 
  hasPermission, 
  level = 0 
}: NavItemComponentProps) {
  const [isOpen, setIsOpen] = React.useState(
    currentPath.startsWith(item.href) || 
    (item.children?.some(child => currentPath.startsWith(child.href)) ?? false)
  );

  // Check if user has permission to see this item
  const hasAccess = !item.permissions || 
    item.permissions.some(permission => hasPermission(permission));

  if (!hasAccess) return null;

  const Icon = item.icon ? iconMap[item.icon] : null;
  const isActive = currentPath === item.href;
  const hasChildren = item.children && item.children.length > 0;
  
  // Filter children based on permissions
  const visibleChildren = item.children?.filter(child => 
    !child.permissions || 
    child.permissions.some(permission => hasPermission(permission))
  ) || [];

  const paddingLeft = level === 0 ? 'pl-3' : level === 1 ? 'pl-6' : 'pl-9';

  if (hasChildren && visibleChildren.length > 0) {
    return (
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            className={cn(
              "w-full justify-start",
              paddingLeft,
              isActive && "bg-accent text-accent-foreground"
            )}
          >
            {Icon && <Icon className="mr-2 h-4 w-4" />}
            <span className="flex-1 text-left">{item.title}</span>
            {isOpen ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-1">
          {visibleChildren.map((child) => (
            <NavItemComponent
              key={child.href}
              item={child}
              currentPath={currentPath}
              hasPermission={hasPermission}
              level={level + 1}
            />
          ))}
        </CollapsibleContent>
      </Collapsible>
    );
  }

  return (
    <Link href={item.href}>
      <Button
        variant="ghost"
        className={cn(
          "w-full justify-start",
          paddingLeft,
          isActive && "bg-accent text-accent-foreground"
        )}
      >
        {Icon && <Icon className="mr-2 h-4 w-4" />}
        {item.title}
      </Button>
    </Link>
  );
}

// Role-specific dashboard shortcuts
interface RoleDashboardShortcutsProps {
  userRole: UserRole;
  className?: string;
}

export function RoleDashboardShortcuts({ userRole, className }: RoleDashboardShortcutsProps) {
  const shortcuts = React.useMemo(() => {
    switch (userRole) {
      case UserRole.SUPER_ADMIN:
        return [
          { title: 'User Management', href: '/dashboard/users', icon: Users },
          { title: 'System Settings', href: '/dashboard/settings', icon: Settings },
          { title: 'Audit Logs', href: '/dashboard/audit-logs', icon: FileText },
        ];
      case UserRole.ADMIN:
        return [
          { title: 'Pending Approvals', href: '/dashboard/permissions/pending', icon: Shield },
          { title: 'Clients', href: '/dashboard/clients', icon: Building2 },
          { title: 'Service Accounts', href: '/dashboard/service-accounts', icon: Key },
        ];
      case UserRole.REQUESTER:
        return [
          { title: 'My Requests', href: '/dashboard/permissions/my-requests', icon: Shield },
          { title: 'New Request', href: '/dashboard/permissions/new', icon: Shield },
          { title: 'My Profile', href: '/dashboard/profile', icon: User },
        ];
      case UserRole.GA_USER:
        return [
          { title: 'My Permissions', href: '/dashboard/permissions/my-requests', icon: Shield },
          { title: 'My Profile', href: '/dashboard/profile', icon: User },
        ];
      default:
        return [];
    }
  }, [userRole]);

  if (shortcuts.length === 0) return null;

  return (
    <div className={cn("space-y-2", className)}>
      <h3 className="text-sm font-medium text-gray-500 px-3">Quick Actions</h3>
      {shortcuts.map((shortcut) => (
        <Link key={shortcut.href} href={shortcut.href}>
          <Button variant="ghost" className="w-full justify-start pl-3">
            <shortcut.icon className="mr-2 h-4 w-4" />
            {shortcut.title}
          </Button>
        </Link>
      ))}
    </div>
  );
}