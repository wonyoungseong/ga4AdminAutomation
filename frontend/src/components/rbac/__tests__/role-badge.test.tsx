/**
 * RoleBadge Component Tests
 * 
 * Comprehensive testing for role badge display component
 * covering role display, Korean labels, status indicators,
 * and styling variations.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { RoleBadge, PermissionBadge, MultiRoleBadge } from '../role-badge';
import { UserRole, UserStatus, PermissionLevel } from '@/types/api';

describe('RoleBadge Component', () => {
  describe('Basic Role Display', () => {
    const roleTestCases: Array<{ role: UserRole; expectedKorean: string; expectedIcon: string }> = [
      { role: 'Super Admin', expectedKorean: '최고 관리자', expectedIcon: '👑' },
      { role: 'Admin', expectedKorean: '관리자', expectedIcon: '🛡️' },
      { role: 'Requester', expectedKorean: '요청자', expectedIcon: '👤' },
      { role: 'Viewer', expectedKorean: '뷰어', expectedIcon: '👁️' },
    ];

    roleTestCases.forEach(({ role, expectedKorean, expectedIcon }) => {
      it(`should display ${role} with Korean label "${expectedKorean}" and icon "${expectedIcon}"`, () => {
        render(<RoleBadge role={role} />);
        
        expect(screen.getByText(expectedKorean)).toBeInTheDocument();
        expect(screen.getByText(expectedIcon)).toBeInTheDocument();
        
        // Check Korean text class
        const koreanText = screen.getByText(expectedKorean);
        expect(koreanText).toHaveClass('korean-text');
      });
    });
  });

  describe('Role-Based Styling', () => {
    it('should apply Super Admin styling', () => {
      render(<RoleBadge role="Super Admin" />);
      
      const badge = screen.getByText('최고 관리자').closest('[class*="bg-red"]');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('border-red-200');
    });

    it('should apply Admin styling', () => {
      render(<RoleBadge role="Admin" />);
      
      const badge = screen.getByText('관리자').closest('[class*="bg-orange"]');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('border-orange-200');
    });

    it('should apply Requester styling', () => {
      render(<RoleBadge role="Requester" />);
      
      const badge = screen.getByText('요청자').closest('[class*="bg-blue"]');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('border-blue-200');
    });

    it('should apply Viewer styling', () => {
      render(<RoleBadge role="Viewer" />);
      
      const badge = screen.getByText('뷰어').closest('[class*="bg-gray"]');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('border-gray-200');
    });
  });

  describe('Status Indicators', () => {
    const statusTestCases: Array<{ status: UserStatus; expectedClass: string; expectedLabel: string }> = [
      { status: 'active', expectedClass: 'ring-green-200', expectedLabel: '활성' },
      { status: 'inactive', expectedClass: 'ring-gray-200', expectedLabel: '비활성' },
      { status: 'suspended', expectedClass: 'ring-red-200', expectedLabel: '정지됨' },
    ];

    statusTestCases.forEach(({ status, expectedClass, expectedLabel }) => {
      it(`should display ${status} status with proper styling and Korean label`, () => {
        render(<RoleBadge role="Admin" status={status} />);
        
        const badge = screen.getByText('관리자').closest('span');
        expect(badge).toHaveClass(expectedClass);
        
        if (status !== 'active') {
          expect(screen.getByText(`• ${expectedLabel}`)).toBeInTheDocument();
        } else {
          expect(screen.queryByText(`• ${expectedLabel}`)).not.toBeInTheDocument();
        }
      });
    });

    it('should apply opacity for inactive status', () => {
      render(<RoleBadge role="Admin" status="inactive" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveClass('opacity-60');
    });

    it('should apply opacity for suspended status', () => {
      render(<RoleBadge role="Admin" status="suspended" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveClass('opacity-75');
    });
  });

  describe('Size Variations', () => {
    const sizeTestCases: Array<{ size: 'sm' | 'md' | 'lg'; expectedClass: string }> = [
      { size: 'sm', expectedClass: 'text-xs px-2 py-1' },
      { size: 'md', expectedClass: 'text-sm px-2.5 py-1' },
      { size: 'lg', expectedClass: 'text-base px-3 py-1.5' },
    ];

    sizeTestCases.forEach(({ size, expectedClass }) => {
      it(`should apply ${size} size styling`, () => {
        render(<RoleBadge role="Admin" size={size} />);
        
        const badge = screen.getByText('관리자').closest('span');
        expect(badge).toHaveClass(expectedClass);
      });
    });
  });

  describe('Custom Props', () => {
    it('should apply custom className', () => {
      render(<RoleBadge role="Admin" className="custom-class" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveClass('custom-class');
    });

    it('should have proper title attribute with Korean text', () => {
      render(<RoleBadge role="Admin" status="inactive" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveAttribute('title', '역할: 관리자 (비활성)');
    });

    it('should have title without status when status is active', () => {
      render(<RoleBadge role="Admin" status="active" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveAttribute('title', '역할: 관리자');
    });
  });

  describe('Accessibility', () => {
    it('should have proper semantic structure', () => {
      render(<RoleBadge role="Admin" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveAttribute('title');
    });

    it('should provide informative title for screen readers', () => {
      render(<RoleBadge role="Super Admin" status="suspended" />);
      
      const badge = screen.getByText('최고 관리자').closest('span');
      expect(badge).toHaveAttribute('title', '역할: 최고 관리자 (정지됨)');
    });

    it('should have proper contrast with transition classes', () => {
      render(<RoleBadge role="Admin" />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveClass('transition-all', 'duration-200');
    });
  });
});

describe('PermissionBadge Component', () => {
  describe('Permission Level Display', () => {
    const permissionLevels: Array<{ level: PermissionLevel; expectedKorean: string; expectedIcon: string }> = [
      { level: 'read', expectedKorean: '읽기', expectedIcon: '👁️' },
      { level: 'edit', expectedKorean: '편집', expectedIcon: '✏️' },
      { level: 'manage', expectedKorean: '관리', expectedIcon: '⚙️' },
    ];

    permissionLevels.forEach(({ level, expectedKorean, expectedIcon }) => {
      it(`should display ${level} permission with Korean label "${expectedKorean}" and icon "${expectedIcon}"`, () => {
        render(<PermissionBadge permission="test.permission" level={level} />);
        
        expect(screen.getByText(expectedKorean)).toBeInTheDocument();
        expect(screen.getByText(expectedIcon)).toBeInTheDocument();
        
        // Check Korean text class
        const koreanText = screen.getByText(expectedKorean);
        expect(koreanText).toHaveClass('korean-text');
      });
    });
  });

  describe('Permission Level Styling', () => {
    it('should apply read permission styling', () => {
      render(<PermissionBadge permission="test.permission" level="read" />);
      
      const badge = screen.getByText('읽기').closest('span');
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('should apply edit permission styling', () => {
      render(<PermissionBadge permission="test.permission" level="edit" />);
      
      const badge = screen.getByText('편집').closest('span');
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('should apply manage permission styling', () => {
      render(<PermissionBadge permission="test.permission" level="manage" />);
      
      const badge = screen.getByText('관리').closest('span');
      expect(badge).toHaveClass('bg-purple-100', 'text-purple-800');
    });
  });

  describe('Permission Properties', () => {
    it('should have proper title attribute with permission details', () => {
      render(<PermissionBadge permission="user.management" level="edit" />);
      
      const badge = screen.getByText('편집').closest('span');
      expect(badge).toHaveAttribute('title', '권한: user.management (편집)');
    });

    it('should apply custom className', () => {
      render(<PermissionBadge permission="test.permission" level="read" className="custom-class" />);
      
      const badge = screen.getByText('읽기').closest('span');
      expect(badge).toHaveClass('custom-class');
    });

    it('should default to read level when no level specified', () => {
      render(<PermissionBadge permission="test.permission" />);
      
      expect(screen.getByText('읽기')).toBeInTheDocument();
      expect(screen.getByText('👁️')).toBeInTheDocument();
    });
  });
});

describe('MultiRoleBadge Component', () => {
  const testRoles: UserRole[] = ['Super Admin', 'Admin', 'Requester', 'Viewer'];

  describe('Multiple Role Display', () => {
    it('should display all roles when count is within maxDisplay limit', () => {
      render(<MultiRoleBadge roles={['Admin', 'Requester']} maxDisplay={3} />);
      
      expect(screen.getByText('관리자')).toBeInTheDocument();
      expect(screen.getByText('요청자')).toBeInTheDocument();
      expect(screen.queryByText('+1개 더')).not.toBeInTheDocument();
    });

    it('should truncate roles and show remainder count when exceeding maxDisplay', () => {
      render(<MultiRoleBadge roles={testRoles} maxDisplay={2} />);
      
      // Should show first 2 roles
      expect(screen.getByText('최고 관리자')).toBeInTheDocument();
      expect(screen.getByText('관리자')).toBeInTheDocument();
      
      // Should show remainder count in Korean
      expect(screen.getByText('+2개 더')).toBeInTheDocument();
      
      // Should not show truncated roles
      expect(screen.queryByText('요청자')).not.toBeInTheDocument();
      expect(screen.queryByText('뷰어')).not.toBeInTheDocument();
    });

    it('should use default maxDisplay of 2', () => {
      render(<MultiRoleBadge roles={testRoles} />);
      
      expect(screen.getByText('최고 관리자')).toBeInTheDocument();
      expect(screen.getByText('관리자')).toBeInTheDocument();
      expect(screen.getByText('+2개 더')).toBeInTheDocument();
    });

    it('should render small-sized badges', () => {
      render(<MultiRoleBadge roles={['Admin']} />);
      
      const badge = screen.getByText('관리자').closest('span');
      expect(badge).toHaveClass('text-xs', 'px-2', 'py-1');
    });
  });

  describe('Layout and Styling', () => {
    it('should apply flex layout with gap', () => {
      render(<MultiRoleBadge roles={['Admin', 'Requester']} />);
      
      const container = screen.getByText('관리자').closest('div');
      expect(container).toHaveClass('flex', 'flex-wrap', 'gap-1');
    });

    it('should apply custom className', () => {
      render(<MultiRoleBadge roles={['Admin']} className="custom-container" />);
      
      const container = screen.getByText('관리자').closest('div');
      expect(container).toHaveClass('custom-container');
    });

    it('should style remainder badge properly', () => {
      render(<MultiRoleBadge roles={testRoles} maxDisplay={1} />);
      
      const remainderBadge = screen.getByText('+3개 더').closest('span');
      expect(remainderBadge).toHaveClass(
        'text-xs',
        'bg-gray-100',
        'text-gray-600'
      );
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty roles array', () => {
      const { container } = render(<MultiRoleBadge roles={[]} />);
      
      expect(container.firstChild).toBeEmptyDOMElement();
    });

    it('should handle single role', () => {
      render(<MultiRoleBadge roles={['Admin']} />);
      
      expect(screen.getByText('관리자')).toBeInTheDocument();
      expect(screen.queryByText('+0개 더')).not.toBeInTheDocument();
    });

    it('should handle maxDisplay larger than roles array', () => {
      render(<MultiRoleBadge roles={['Admin', 'Requester']} maxDisplay={5} />);
      
      expect(screen.getByText('관리자')).toBeInTheDocument();
      expect(screen.getByText('요청자')).toBeInTheDocument();
      expect(screen.queryByText('+0개 더')).not.toBeInTheDocument();
    });

    it('should handle duplicate roles', () => {
      render(<MultiRoleBadge roles={['Admin', 'Admin', 'Requester']} maxDisplay={3} />);
      
      // Should render all badges, even duplicates
      const adminBadges = screen.getAllByText('관리자');
      expect(adminBadges).toHaveLength(2);
      expect(screen.getByText('요청자')).toBeInTheDocument();
    });
  });
});

describe('Korean Localization', () => {
  it('should display all role names in Korean', () => {
    const roles: UserRole[] = ['Super Admin', 'Admin', 'Requester', 'Viewer'];
    const expectedKorean = ['최고 관리자', '관리자', '요청자', '뷰어'];
    
    roles.forEach((role, index) => {
      const { unmount } = render(<RoleBadge role={role} />);
      expect(screen.getByText(expectedKorean[index])).toBeInTheDocument();
      unmount();
    });
  });

  it('should display all status labels in Korean', () => {
    const statuses: UserStatus[] = ['active', 'inactive', 'suspended'];
    const expectedLabels = ['활성', '비활성', '정지됨'];
    
    statuses.forEach((status, index) => {
      const { unmount } = render(<RoleBadge role="Admin" status={status} />);
      
      if (status !== 'active') {
        expect(screen.getByText(`• ${expectedLabels[index]}`)).toBeInTheDocument();
      }
      unmount();
    });
  });

  it('should display all permission levels in Korean', () => {
    const levels: PermissionLevel[] = ['read', 'edit', 'manage'];
    const expectedKorean = ['읽기', '편집', '관리'];
    
    levels.forEach((level, index) => {
      const { unmount } = render(<PermissionBadge permission="test" level={level} />);
      expect(screen.getByText(expectedKorean[index])).toBeInTheDocument();
      unmount();
    });
  });

  it('should use Korean text for remainder count', () => {
    render(<MultiRoleBadge roles={['Admin', 'Requester', 'Viewer']} maxDisplay={1} />);
    
    expect(screen.getByText('+2개 더')).toBeInTheDocument();
  });
});

describe('Performance and Optimization', () => {
  it('should render efficiently with many roles', () => {
    const start = performance.now();
    
    const manyRoles: UserRole[] = Array(100).fill('Admin');
    render(<MultiRoleBadge roles={manyRoles} maxDisplay={5} />);
    
    const end = performance.now();
    expect(end - start).toBeLessThan(100); // Should render in less than 100ms
    
    // Should only render maxDisplay + 1 (remainder) badges
    const badges = document.querySelectorAll('[class*="bg-"]');
    expect(badges.length).toBeLessThanOrEqual(6);
  });

  it('should not cause memory leaks with frequent re-renders', () => {
    const TestComponent = ({ role }: { role: UserRole }) => <RoleBadge role={role} />;
    
    const { rerender } = render(<TestComponent role="Admin" />);
    
    // Simulate many re-renders
    for (let i = 0; i < 100; i++) {
      rerender(<TestComponent role={i % 2 === 0 ? 'Admin' : 'Requester'} />);
    }
    
    // Should still render correctly
    expect(screen.getByText(i % 2 === 0 ? '관리자' : '요청자')).toBeInTheDocument();
  });
});

describe('Theme Support', () => {
  it('should have dark mode classes for role badges', () => {
    render(<RoleBadge role="Admin" />);
    
    const badge = screen.getByText('관리자').closest('span');
    expect(badge).toHaveClass('dark:bg-orange-900', 'dark:text-orange-200');
  });

  it('should have dark mode classes for permission badges', () => {
    render(<PermissionBadge permission="test" level="read" />);
    
    const badge = screen.getByText('읽기').closest('span');
    expect(badge).toHaveClass('dark:bg-green-900', 'dark:text-green-200');
  });

  it('should have dark mode classes for remainder badge', () => {
    render(<MultiRoleBadge roles={['Admin', 'Requester', 'Viewer']} maxDisplay={1} />);
    
    const remainderBadge = screen.getByText('+2개 더').closest('span');
    expect(remainderBadge).toHaveClass('dark:bg-gray-800', 'dark:text-gray-400');
  });
});