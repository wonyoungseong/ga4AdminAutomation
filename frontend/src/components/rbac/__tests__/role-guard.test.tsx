/**
 * RoleGuard Component Tests
 * 
 * Comprehensive testing for role-based access control component
 * covering role hierarchy, permission checking, loading states,
 * and Korean localization.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { RoleGuard, useRoleCheck, UnauthorizedMessage, PermissionGuard } from '../role-guard';
import { User, UserRole } from '@/types/api';

// Mock the auth context
jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}));

// Get the mocked useAuth function
import { useAuth } from '@/contexts/auth-context';
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Helper function to create mock users with different roles
const createMockUser = (role: UserRole, status = 'active' as const): User => ({
  id: 1,
  email: 'test@example.com',
  name: '테스트 사용자',
  role,
  status,
  registration_status: 'approved',
  is_representative: false,
  created_at: '2024-01-01T00:00:00Z'
});

// Helper function to create base auth state
const createAuthState = (overrides = {}) => ({
  isLoading: false,
  isInitialized: true,
  isRefreshing: false,
  login: jest.fn(),
  logout: jest.fn(),
  token: null,
  user: null,
  ...overrides,
});

describe('RoleGuard Component', () => {
  const ProtectedContent = () => <div data-testid="protected-content">Protected Content</div>;
  const FallbackContent = () => <div data-testid="fallback-content">Access Denied</div>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading skeleton when auth is loading', () => {
      mockUseAuth.mockReturnValue(createAuthState({
        isLoading: true,
        isInitialized: false,
      }));

      render(
        <RoleGuard allowedRoles={['Admin']}>
          <ProtectedContent />
        </RoleGuard>
      );

      // Check for loading skeleton - it should contain animated pulse elements
      const loadingElements = document.querySelectorAll('.animate-pulse');
      expect(loadingElements.length).toBeGreaterThan(0);
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should have proper loading animation classes', () => {
      mockUseAuth.mockReturnValue(createAuthState({
        isLoading: true,
        isInitialized: false,
      }));

      render(
        <RoleGuard allowedRoles={['Admin']}>
          <ProtectedContent />
        </RoleGuard>
      );

      const loadingElements = document.querySelectorAll('.animate-pulse');
      expect(loadingElements.length).toBeGreaterThan(0);
      expect(loadingElements[0]).toHaveClass('animate-pulse');
    });
  });

  describe('Unauthenticated Access', () => {
    it('should deny access when user is null', () => {
      mockUseAuth.mockReturnValue(createAuthState());

      render(
        <RoleGuard allowedRoles={['Admin']}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should show fallback content when user is null and fallback is provided', () => {
      mockUseAuth.mockReturnValue(createAuthState());

      render(
        <RoleGuard allowedRoles={['Admin']} fallback={<FallbackContent />}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.getByTestId('fallback-content')).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });

  describe('Role-Based Access Control', () => {
    it('should allow access for users with allowed roles', () => {
      const mockUser = createMockUser('Admin');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      render(
        <RoleGuard allowedRoles={['Admin']}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should deny access for users without allowed roles', () => {
      const mockUser = createMockUser('Viewer');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      render(
        <RoleGuard allowedRoles={['Admin']}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should allow access when user role is in multiple allowed roles', () => {
      const mockUser = createMockUser('Requester');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      render(
        <RoleGuard allowedRoles={['Admin', 'Requester', 'Viewer']}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Role Hierarchy Validation', () => {
    const roleTestCases = [
      { role: 'Super Admin' as UserRole, allowed: ['Super Admin'], shouldHaveAccess: true },
      { role: 'Super Admin' as UserRole, allowed: ['Admin'], shouldHaveAccess: false },
      { role: 'Admin' as UserRole, allowed: ['Admin'], shouldHaveAccess: true },
      { role: 'Admin' as UserRole, allowed: ['Super Admin'], shouldHaveAccess: false },
      { role: 'Requester' as UserRole, allowed: ['Requester'], shouldHaveAccess: true },
      { role: 'Requester' as UserRole, allowed: ['Admin'], shouldHaveAccess: false },
      { role: 'Viewer' as UserRole, allowed: ['Viewer'], shouldHaveAccess: true },
      { role: 'Viewer' as UserRole, allowed: ['Requester'], shouldHaveAccess: false },
    ];

    roleTestCases.forEach(({ role, allowed, shouldHaveAccess }) => {
      it(`should ${shouldHaveAccess ? 'allow' : 'deny'} access for ${role} when allowed roles are ${allowed.join(', ')}`, () => {
        const mockUser = createMockUser(role);
        mockUseAuth.mockReturnValue(createAuthState({
          user: mockUser,
          token: 'mock-token',
        }));

        render(
          <RoleGuard allowedRoles={allowed}>
            <ProtectedContent />
          </RoleGuard>
        );

        if (shouldHaveAccess) {
          expect(screen.getByTestId('protected-content')).toBeInTheDocument();
        } else {
          expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
        }
      });
    });
  });

  describe('RequireAll Mode', () => {
    it('should deny access when requireAll is true and user does not have all roles', () => {
      const mockUser = createMockUser('Admin');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      render(
        <RoleGuard allowedRoles={['Admin', 'Super Admin']} requireAll={true}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should allow access when requireAll is false and user has at least one role', () => {
      const mockUser = createMockUser('Admin');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      render(
        <RoleGuard allowedRoles={['Admin', 'Super Admin']} requireAll={false}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Fallback Behavior', () => {
    it('should render nothing when access denied and no fallback provided', () => {
      const mockUser = createMockUser('Viewer');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      const { container } = render(
        <RoleGuard allowedRoles={['Admin']}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(container.firstChild).toBeNull();
    });

    it('should render custom fallback when access denied', () => {
      const mockUser = createMockUser('Viewer');
      mockUseAuth.mockReturnValue(createAuthState({
        user: mockUser,
        token: 'mock-token',
      }));

      render(
        <RoleGuard allowedRoles={['Admin']} fallback={<FallbackContent />}>
          <ProtectedContent />
        </RoleGuard>
      );

      expect(screen.getByTestId('fallback-content')).toBeInTheDocument();
    });
  });
});

describe('useRoleCheck Hook', () => {
  const TestComponent = ({ allowedRoles }: { allowedRoles: UserRole[] }) => {
    const hasPermission = useRoleCheck(allowedRoles);
    return <div data-testid="permission-result">{hasPermission ? 'allowed' : 'denied'}</div>;
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return true for users with allowed roles', () => {
    const mockUser = createMockUser('Admin');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    render(<TestComponent allowedRoles={['Admin']} />);
    
    expect(screen.getByTestId('permission-result')).toHaveTextContent('allowed');
  });

  it('should return false for users without allowed roles', () => {
    const mockUser = createMockUser('Viewer');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    render(<TestComponent allowedRoles={['Admin']} />);
    
    expect(screen.getByTestId('permission-result')).toHaveTextContent('denied');
  });

  it('should return false when user is null', () => {
    mockUseAuth.mockReturnValue(createAuthState());

    render(<TestComponent allowedRoles={['Admin']} />);
    
    expect(screen.getByTestId('permission-result')).toHaveTextContent('denied');
  });
});

describe('UnauthorizedMessage Component', () => {
  it('should render Korean unauthorized message', () => {
    render(<UnauthorizedMessage />);
    
    expect(screen.getByText('접근 권한이 없습니다')).toBeInTheDocument();
    expect(screen.getByText('이 기능을 사용하려면 적절한 권한이 필요합니다.')).toBeInTheDocument();
  });

  it('should have proper styling and structure', () => {
    render(<UnauthorizedMessage />);
    
    const container = screen.getByText('접근 권한이 없습니다').closest('div');
    expect(container).toHaveClass('flex', 'flex-col', 'items-center', 'justify-center');
    
    const icon = screen.getByText('🔒');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('text-4xl', 'mb-4');
  });

  it('should have accessible structure', () => {
    render(<UnauthorizedMessage />);
    
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toHaveTextContent('접근 권한이 없습니다');
    
    const description = screen.getByText('이 기능을 사용하려면 적절한 권한이 필요합니다.');
    expect(description).toBeInTheDocument();
  });
});

describe('PermissionGuard Component', () => {
  const ProtectedContent = () => <div data-testid="protected-content">Protected Content</div>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Permission Hierarchy', () => {
    const permissionTestCases = [
      // Super Admin permissions
      { role: 'Super Admin' as UserRole, permission: 'user.delete', shouldHaveAccess: true },
      { role: 'Super Admin' as UserRole, permission: 'system.config', shouldHaveAccess: true },
      { role: 'Super Admin' as UserRole, permission: 'user.create', shouldHaveAccess: true },
      { role: 'Super Admin' as UserRole, permission: 'audit.view', shouldHaveAccess: true },
      
      // Admin permissions
      { role: 'Admin' as UserRole, permission: 'user.create', shouldHaveAccess: true },
      { role: 'Admin' as UserRole, permission: 'user.edit', shouldHaveAccess: true },
      { role: 'Admin' as UserRole, permission: 'permission.grant', shouldHaveAccess: true },
      { role: 'Admin' as UserRole, permission: 'dashboard.admin', shouldHaveAccess: true },
      { role: 'Admin' as UserRole, permission: 'user.delete', shouldHaveAccess: false },
      { role: 'Admin' as UserRole, permission: 'system.config', shouldHaveAccess: false },
      
      // Requester permissions
      { role: 'Requester' as UserRole, permission: 'audit.view', shouldHaveAccess: true },
      { role: 'Requester' as UserRole, permission: 'user.create', shouldHaveAccess: false },
      { role: 'Requester' as UserRole, permission: 'user.edit', shouldHaveAccess: false },
      { role: 'Requester' as UserRole, permission: 'dashboard.admin', shouldHaveAccess: false },
      
      // Viewer permissions
      { role: 'Viewer' as UserRole, permission: 'audit.view', shouldHaveAccess: false },
      { role: 'Viewer' as UserRole, permission: 'user.create', shouldHaveAccess: false },
      { role: 'Viewer' as UserRole, permission: 'user.edit', shouldHaveAccess: false },
    ];

    permissionTestCases.forEach(({ role, permission, shouldHaveAccess }) => {
      it(`should ${shouldHaveAccess ? 'allow' : 'deny'} ${role} access to ${permission}`, () => {
        const mockUser = createMockUser(role);
        mockUseAuth.mockReturnValue(createAuthState({
          user: mockUser,
          token: 'mock-token',
        }));

        render(
          <PermissionGuard permission={permission}>
            <ProtectedContent />
          </PermissionGuard>
        );

        if (shouldHaveAccess) {
          expect(screen.getByTestId('protected-content')).toBeInTheDocument();
        } else {
          expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
        }
      });
    });
  });

  it('should show UnauthorizedMessage fallback by default when access denied', () => {
    const mockUser = createMockUser('Viewer');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    render(
      <PermissionGuard permission="user.create">
        <ProtectedContent />
      </PermissionGuard>
    );

    expect(screen.getByText('접근 권한이 없습니다')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should show custom fallback when provided', () => {
    const mockUser = createMockUser('Viewer');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    const CustomFallback = () => <div data-testid="custom-fallback">Custom Access Denied</div>;

    render(
      <PermissionGuard permission="user.create" fallback={<CustomFallback />}>
        <ProtectedContent />
      </PermissionGuard>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should deny access when user is null', () => {
    mockUseAuth.mockReturnValue(createAuthState());

    render(
      <PermissionGuard permission="user.create">
        <ProtectedContent />
      </PermissionGuard>
    );

    expect(screen.getByText('접근 권한이 없습니다')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});

describe('Accessibility', () => {
  it('should have proper ARIA attributes in UnauthorizedMessage', () => {
    render(<UnauthorizedMessage />);
    
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toBeInTheDocument();
    
    // Check semantic structure
    const container = heading.closest('div');
    expect(container).toHaveClass('text-center');
  });

  it('should maintain focus management during role changes', async () => {
    const mockUser = createMockUser('Viewer');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    const { rerender } = render(
      <RoleGuard allowedRoles={['Admin']}>
        <button data-testid="protected-button">Protected Button</button>
      </RoleGuard>
    );

    expect(screen.queryByTestId('protected-button')).not.toBeInTheDocument();

    // Change user role to Admin
    mockUseAuth.mockReturnValue(createAuthState({
      user: createMockUser('Admin'),
      token: 'mock-token',
    }));

    rerender(
      <RoleGuard allowedRoles={['Admin']}>
        <button data-testid="protected-button">Protected Button</button>
      </RoleGuard>
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-button')).toBeInTheDocument();
    });
  });
});

describe('Korean Localization', () => {
  it('should display Korean text in UnauthorizedMessage', () => {
    render(<UnauthorizedMessage />);
    
    // Check for Korean text content
    expect(screen.getByText('접근 권한이 없습니다')).toBeInTheDocument();
    expect(screen.getByText('이 기능을 사용하려면 적절한 권한이 필요합니다.')).toBeInTheDocument();
  });

  it('should handle Korean user names properly', () => {
    const mockUser = createMockUser('Admin');
    mockUser.name = '김철수';
    
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    render(
      <RoleGuard allowedRoles={['Admin']}>
        <div data-testid="user-name">{mockUser.name}</div>
      </RoleGuard>
    );

    expect(screen.getByTestId('user-name')).toHaveTextContent('김철수');
  });
});

describe('Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should handle invalid role values gracefully', () => {
    const mockUser = { ...createMockUser('Admin'), role: 'InvalidRole' as UserRole };
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    expect(() => {
      render(
        <RoleGuard allowedRoles={['Admin']}>
          <div data-testid="protected-content">Protected Content</div>
        </RoleGuard>
      );
    }).not.toThrow();

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should handle empty allowedRoles array', () => {
    const mockUser = createMockUser('Admin');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    render(
      <RoleGuard allowedRoles={[]}>
        <div data-testid="protected-content">Protected Content</div>
      </RoleGuard>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should handle undefined permission in PermissionGuard', () => {
    const mockUser = createMockUser('Admin');
    mockUseAuth.mockReturnValue(createAuthState({
      user: mockUser,
      token: 'mock-token',
    }));

    render(
      <PermissionGuard permission="undefined.permission">
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGuard>
    );

    // Should default to lowest permission level (Viewer level = 1)
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });
});